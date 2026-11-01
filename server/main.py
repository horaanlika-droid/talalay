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
import secrets
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("embassy")

# ------------------------------------------------------------------ admin auth
_ADMIN_TOKENS: dict[str, float] = {}   # token -> expiry timestamp
_ADMIN_TTL_SECONDS = 60 * 60 * 24      # 24 h session


def _require_admin(request: Request) -> None:
    """401 unless a valid admin session token is presented."""
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="admin login required")
    token = auth[7:]
    expiry = _ADMIN_TOKENS.get(token)
    if not expiry or time.time() > expiry:
        _ADMIN_TOKENS.pop(token, None)
        raise HTTPException(status_code=401, detail="admin session expired")


def _issue_admin_token() -> str:
    token = secrets.token_urlsafe(24)
    _ADMIN_TOKENS[token] = time.time() + _ADMIN_TTL_SECONDS
    return token


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


# ================================================================ admin API

class AdminLoginIn(BaseModel):
    password: str


@app.post("/api/admin/login")
async def admin_login(payload: AdminLoginIn) -> JSONResponse:
    if not cfg.ADMIN_PASSWORD:
        raise HTTPException(status_code=500, detail="admin password not configured")
    if payload.password != cfg.ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="wrong password")
    return JSONResponse({"ok": True, "token": _issue_admin_token()})


@app.get("/api/admin/content")
async def admin_content(request: Request) -> JSONResponse:
    _require_admin(request)
    return JSONResponse(db.get_content())


class SettingsIn(BaseModel):
    key: str
    value: Any


@app.put("/api/admin/settings")
async def admin_set_setting(payload: SettingsIn, request: Request) -> JSONResponse:
    _require_admin(request)
    db.set_setting(payload.key, payload.value)
    return JSONResponse({"ok": True})


@app.put("/api/admin/products/{slug}")
async def admin_update_product(slug: str, payload: dict, request: Request) -> JSONResponse:
    _require_admin(request)
    db.upsert_product(
        slug=slug,
        name=payload.get("name", ""),
        subtitle=payload.get("subtitle", ""),
        description=payload.get("description", ""),
        price=float(payload.get("price") or 0),
        volume=payload.get("volume", ""),
        category_slug=payload.get("categorySlug", ""),
        badge=payload.get("badge", ""),
        featured=bool(payload.get("featured")),
        in_stock=bool(payload.get("inStock", True)),
        sort=int(payload.get("sort") or 0),
        images=payload.get("images", []),
        collections=payload.get("collectionSlugs", []),
        specs=payload.get("specs", {}),
    )
    return JSONResponse({"ok": True})


@app.post("/api/admin/products")
async def admin_create_product(payload: dict, request: Request) -> JSONResponse:
    _require_admin(request)
    slug = payload.get("slug") or db.slugify(payload.get("name", "item"))
    db.upsert_product(
        slug=slug,
        name=payload.get("name", ""),
        subtitle=payload.get("subtitle", ""),
        description=payload.get("description", ""),
        price=float(payload.get("price") or 0),
        volume=payload.get("volume", ""),
        category_slug=payload.get("categorySlug", ""),
        badge=payload.get("badge", ""),
        featured=bool(payload.get("featured")),
        in_stock=bool(payload.get("inStock", True)),
        sort=int(payload.get("sort") or 0),
        images=payload.get("images", []),
        collections=payload.get("collectionSlugs", []),
        specs=payload.get("specs", {}),
    )
    return JSONResponse({"ok": True, "slug": slug})


@app.delete("/api/admin/products/{slug}")
async def admin_delete_product(slug: str, request: Request) -> JSONResponse:
    _require_admin(request)
    db.delete_product(slug)
    return JSONResponse({"ok": True})


@app.put("/api/admin/categories/{slug}")
async def admin_update_category(slug: str, payload: dict, request: Request) -> JSONResponse:
    _require_admin(request)
    db.upsert_category(
        slug=slug,
        name=payload.get("name", ""),
        blurb=payload.get("blurb", ""),
        sort=int(payload.get("sort") or 0),
    )
    return JSONResponse({"ok": True})


@app.put("/api/admin/collections/{slug}")
async def admin_update_collection(slug: str, payload: dict, request: Request) -> JSONResponse:
    _require_admin(request)
    db.upsert_collection(
        slug=slug,
        name=payload.get("name", ""),
        subtitle=payload.get("subtitle", ""),
        description=payload.get("description", ""),
        image=payload.get("image", ""),
        sort=int(payload.get("sort") or 0),
    )
    return JSONResponse({"ok": True})


@app.get("/api/admin/requests")
async def admin_list_requests(request: Request, status: str | None = None) -> JSONResponse:
    _require_admin(request)
    return JSONResponse(db.list_requests(status=status))


@app.post("/api/admin/requests/{request_id}/status")
async def admin_set_request_status(
    request: Request, request_id: int, payload: dict
) -> JSONResponse:
    _require_admin(request)
    db.set_request_status(request_id, payload.get("status", "new"))
    return JSONResponse({"ok": True})


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
