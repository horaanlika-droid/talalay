"""Cocktail Embassy — API + Telegram back office (single process for BotHost)."""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

import db
import settings as cfg

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("embassy")


class RequestItem(BaseModel):
    slug: str = Field(min_length=1, max_length=120)
    name: str = Field(default="", max_length=200)
    qty: int = Field(default=1, ge=1, le=999)
    price: float | None = None


class RequestIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    company: str = Field(default="", max_length=160)
    email: str = Field(min_length=3, max_length=160)
    phone: str = Field(default="", max_length=60)
    country: str = Field(default="", max_length=80)
    city: str = Field(default="", max_length=80)
    address: str = Field(default="", max_length=240)
    taxId: str = Field(default="", max_length=40)
    delivery: str = Field(default="", max_length=32)
    payment: str = Field(default="", max_length=32)
    shipping: float | None = None
    note: str = Field(default="", max_length=2000)
    items: list[RequestItem] = Field(min_length=1, max_length=100)
    total: float | None = None
    currency: str = Field(default="AED", max_length=8)
    source: str = Field(default="web", max_length=32)

    @field_validator("email")
    @classmethod
    def valid_email(cls, value: str) -> str:
        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError("Invalid email address")
        return value.strip()


class RequestOut(BaseModel):
    ok: bool = True
    id: int
    reference: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    cfg.MEDIA_DIR.mkdir(parents=True, exist_ok=True)

    bot_task = None
    if cfg.RUN_BOT and cfg.BOT_TOKEN:
        import telegram_bot

        bot_task = asyncio.create_task(telegram_bot.run_polling())
        log.info("Telegram polling started")
    elif cfg.RUN_BOT:
        log.warning("TELEGRAM_BOT_TOKEN is empty — running API only")

    yield

    if bot_task:
        bot_task.cancel()
        try:
            await bot_task
        except (asyncio.CancelledError, Exception):  # noqa: BLE001
            pass


app = FastAPI(title="Cocktail Embassy API", version="1.0.0", lifespan=lifespan)

cfg.MEDIA_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(cfg.MEDIA_DIR)), name="media")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cfg.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def no_store(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


@app.get("/")
async def index() -> dict[str, Any]:
    return {
        "service": "Cocktail Embassy API",
        "status": "ok",
        "endpoints": ["/api/content", "/api/requests", "/api/health", "/media/<file>"],
    }


@app.get("/api/health")
async def health() -> dict[str, Any]:
    return {
        "ok": True,
        "products": len(db.list_products()),
        "requests": db.request_counts(),
        "bot": bool(cfg.BOT_TOKEN),
    }


@app.get("/api/content")
async def content() -> JSONResponse:
    return JSONResponse(db.get_content())


def _shipping_for(settings: dict, delivery: str, subtotal: float) -> float:
    """Shipping the office will invoice for this order.

    The method list lives in settings, so the shop owner can change a fee from
    the bot without a deploy. Free above the threshold, free on pickup; a method
    with fee 0 and no threshold means "quoted later" and adds nothing here.
    """
    methods = settings.get("deliveryMethods") or []
    method = next((m for m in methods if m.get("id") == delivery), None)
    if not method:
        return 0.0
    fee = float(method.get("fee") or 0)
    threshold = float(settings.get("freeShippingFrom") or 0)
    if method.get("id") == "pickup" or fee <= 0:
        return 0.0
    if threshold and subtotal >= threshold:
        return 0.0
    return fee


@app.post("/api/requests", response_model=RequestOut)
async def create_request(payload: RequestIn) -> RequestOut:
    products = {p["slug"]: p for p in db.list_products()}
    items: list[dict[str, Any]] = []
    total = 0.0
    for item in payload.items:
        product = products.get(item.slug)
        price = float(product["price"]) if product else float(item.price or 0)
        name = product["name"] if product else item.name
        items.append(
            {
                "slug": item.slug,
                "name": name,
                "qty": item.qty,
                "price": price,
                "sum": round(price * item.qty, 2),
            }
        )
        total += price * item.qty

    settings = db.all_settings()
    subtotal = round(total if total else float(payload.total or 0), 2)
    shipping = _shipping_for(settings, payload.delivery, subtotal)

    record = db.create_request(
        {
            "name": payload.name.strip(),
            "company": payload.company.strip(),
            "email": payload.email.strip(),
            "phone": payload.phone.strip(),
            "country": payload.country.strip(),
            "city": payload.city.strip(),
            "address": payload.address.strip(),
            "taxId": payload.taxId.strip(),
            "delivery": payload.delivery.strip(),
            "payment": payload.payment.strip(),
            "shipping": shipping,
            "note": payload.note.strip(),
            "items": items,
            "total": subtotal,
            "currency": payload.currency,
        }
    )
    log.info("New request %s from %s (%s items)", record["reference"], record["email"], len(items))

    if cfg.RUN_BOT and cfg.BOT_TOKEN:
        try:
            import telegram_bot

            asyncio.create_task(telegram_bot.notify_new_request(record))
        except Exception as exc:  # noqa: BLE001
            log.warning("Bot notification failed: %s", exc)

    return RequestOut(id=record["id"], reference=record["reference"])


@app.exception_handler(ValueError)
async def value_error_handler(_: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


def main() -> None:
    if not cfg.BOT_TOKEN:
        log.warning("TELEGRAM_BOT_TOKEN is not set. The admin bot will not start.")
    log.info("Starting API on %s:%s", cfg.HOST, cfg.PORT)
    uvicorn.run("main:app", host=cfg.HOST, port=cfg.PORT, log_level="info", proxy_headers=True)


if __name__ == "__main__":
    main()
