"""Telegram back office for Cocktail Embassy.

Everything the storefront shows — products, categories, collections, hero slides,
contact details and copy — is edited here and served to the site via /api/content.

Run with the API (see main.py) or standalone: `python telegram_bot.py`.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ChatAction
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import db
import settings as cfg

log = logging.getLogger("embassy.bot")

router = Router()

PAGE_SIZE = 6
CURRENCY_SYMBOLS = {"EUR": "€", "USD": "$", "AED": "AED ", "GBP": "£"}


def money(amount: float) -> str:
    currency = db.get_setting("currency", "EUR") or "EUR"
    symbol = CURRENCY_SYMBOLS.get(currency, f"{currency} ")
    value = f"{amount:,.2f}".rstrip("0").rstrip(".") if amount % 1 else f"{amount:,.0f}"
    return f"{symbol}{value}"


def kb(rows: list[list[tuple[str, str]]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=text, callback_data=data) for text, data in row] for row in rows
        ]
    )


def clip(value: str, limit: int = 40) -> str:
    value = (value or "").strip().replace("\n", " ")
    return value if len(value) <= limit else value[: limit - 1] + "…"


# --------------------------------------------------------------------- states
class EditText(StatesGroup):
    value = State()


class NewCategory(StatesGroup):
    name = State()


class NewCollection(StatesGroup):
    name = State()


class NewProduct(StatesGroup):
    name = State()
    price = State()


class UploadPhoto(StatesGroup):
    photo = State()


class Search(StatesGroup):
    query = State()


class AskPassword(StatesGroup):
    password = State()


# ----------------------------------------------------------------- middleware
def is_owner(user_id: int) -> bool:
    return bool(cfg.ADMIN_IDS) and user_id in cfg.ADMIN_IDS


def is_authorised(user_id: int) -> bool:
    """Owner IDs are always allowed; staff pass once they enter the password."""
    if is_owner(user_id):
        return True
    return db.is_staff(user_id)


class AdminOnly:
    """Gate every update behind the owner ID list or the bot password."""

    async def __call__(self, handler, event, data):
        user = data.get("event_from_user")
        if user and is_authorised(user.id):
            return await handler(event, data)

        # Let the password step and the public commands through.
        fsm = data.get("state")
        if fsm is not None and await fsm.get_state() == AskPassword.password.state:
            return await handler(event, data)
        if isinstance(event, Message):
            command = (event.text or "").split()[0].split("@")[0].lower() if event.text else ""
            if command in ("/start", "/login", "/auth", "/cancel", "/id", "/logout"):
                return await handler(event, data)

        # Unauthenticated: offer the password screen.
        if isinstance(event, CallbackQuery):
            await event.answer("Password required", show_alert=True)
            await login_screen(event.message, event.from_user.id)
            return None
        if isinstance(event, Message):
            await login_screen(event, user.id if user else 0)
            return None
        return None


async def login_screen(target: Message, user_id: int) -> None:
    """Explain how to get in, without leaking the password."""
    if not cfg.ADMIN_PASSWORD:
        text = (
            "🔒 This is a private back office.\n\n"
            f"Your Telegram ID: {user_id}\n\n"
            "No password is configured on the server yet. Ask the owner to set "
            "ADMIN_PASSWORD (or add your ID to ADMIN_ID) in the BotHost variables."
        )
        markup = None
    else:
        text = (
            "🔒 Cocktail Embassy — back office\n\n"
            "Send the admin password to continue.\n\n"
            f"Your Telegram ID: {user_id}"
        )
        markup = kb([[("🔑 Enter password", "auth:login")]])
    try:
        await target.answer(text, reply_markup=markup)
    except Exception:  # noqa: BLE001
        pass


# --------------------------------------------------------------------- menus
def main_menu_text() -> str:
    counts = db.request_counts()
    products = db.list_products()
    out_of_stock = sum(1 for p in products if not p["inStock"])
    return (
        "🏛  COCKTAIL EMBASSY — back office\n\n"
        f"Pieces: {len(products)}   ·   Categories: {len(db.list_categories())}   ·   Collections: {len(db.list_collections())}\n"
        f"New requests: {counts['new']}   ·   Out of stock: {out_of_stock}\n\n"
        "Everything you change here appears on the website within seconds."
    )


def main_menu_kb() -> InlineKeyboardMarkup:
    counts = db.request_counts()
    return kb(
        [
            [("📦  Products", "prod:list:0"), ("🎨  Collections", "coll:list")],
            [("🗂  Categories", "cat:list"), ("⚙️  Site & content", "set:menu")],
            [(f"🧾  Requests · {counts['new']} new", "req:list:new:0")],
            [("📊  Overview", "stats"), ("❓  Help", "help")],
            [("🌐  Open storefront", "link:site")],
        ]
    )


async def show_main_menu(target: Message | CallbackQuery, state: FSMContext | None = None) -> None:
    if state:
        await state.clear()
    text, markup = main_menu_text(), main_menu_kb()
    if isinstance(target, CallbackQuery):
        await safe_edit(target.message, text, markup)
        await target.answer()
    else:
        await target.answer(text, reply_markup=markup)


async def safe_edit(message: Message, text: str, markup: InlineKeyboardMarkup | None = None) -> None:
    if not hasattr(message, "edit_text"):
        await message.answer(text, reply_markup=markup, disable_web_page_preview=True)
        return
    try:
        await message.edit_text(text, reply_markup=markup, disable_web_page_preview=True)
    except TelegramBadRequest as exc:
        if "message is not modified" in str(exc):
            return
        try:
            await message.answer(text, reply_markup=markup, disable_web_page_preview=True)
        except Exception:  # noqa: BLE001
            log.warning("Could not render message: %s", exc)


# ------------------------------------------------------------------ commands
@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await show_main_menu(message, state)


@router.message(Command("menu", "admin"))
async def menu(message: Message, state: FSMContext) -> None:
    await show_main_menu(message, state)


@router.message(Command("id"))
async def whoami(message: Message) -> None:
    await message.answer(f"Your Telegram ID: {message.from_user.id}")


@router.message(Command("login", "auth"))
async def cmd_login(message: Message, state: FSMContext) -> None:
    if is_authorised(message.from_user.id):
        await show_main_menu(message, state)
        return
    await state.set_state(AskPassword.password)
    await message.answer("🔑 Send the admin password. /cancel to abort.")


@router.message(Command("logout"))
async def cmd_logout(message: Message, state: FSMContext) -> None:
    await state.clear()
    if is_owner(message.from_user.id):
        await message.answer("You are the owner — access is granted by ADMIN_ID and cannot be logged out.")
        return
    db.revoke_staff(message.from_user.id)
    await message.answer("Logged out. Send /login to sign in again.")


@router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Cancelled.", reply_markup=main_menu_kb())


@router.callback_query(F.data == "menu")
async def cb_menu(call: CallbackQuery, state: FSMContext) -> None:
    await show_main_menu(call, state)


@router.callback_query(F.data == "auth:login")
async def cb_login(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AskPassword.password)
    try:
        await call.message.edit_text("🔑 Send the admin password. /cancel to abort.")
    except TelegramBadRequest:
        await call.message.answer("🔑 Send the admin password. /cancel to abort.")
    await call.answer()


@router.callback_query(F.data == "help")
async def cb_help(call: CallbackQuery) -> None:
    await safe_edit(
        call.message,
        "How this works\n\n"
        "• Products — add pieces, change price, copy, photos, stock and collections.\n"
        "• Collections — the four tiles on the home page.\n"
        "• Categories — Glassware / Barware / Acids & Other.\n"
        "• Site & content — brand name, hero slides, announcement, contacts, legal notes.\n"
        "• Requests — every request sent from the website lands here.\n\n"
        "A photo sent to a product becomes its catalogue image. The first photo is the cover.\n\n"
        "Access: the owner (ADMIN_ID) is always signed in. Anyone else enters ADMIN_PASSWORD once and stays "
        f"signed in for {cfg.AUTH_TTL_HOURS} hours.\n\n"
        "Commands: /menu · /login · /logout · /cancel · /id",
        kb([[("⬅️  Back", "menu")]]),
    )
    await call.answer()


@router.callback_query(F.data == "stats")
async def cb_stats(call: CallbackQuery) -> None:
    products = db.list_products()
    counts = db.request_counts()
    recent = db.list_requests("all", 3)
    lines = [
        "📊  Overview\n",
        f"Pieces: {len(products)}   ·   In stock: {sum(1 for p in products if p['inStock'])}",
        f"Featured: {sum(1 for p in products if p['featured'])}   ·   Categories: {len(db.list_categories())}",
        f"Collections: {len(db.list_collections())}\n",
        f"Requests — new: {counts['new']} · in progress: {counts['processing']} · done: {counts['done']}\n",
    ]
    if recent:
        lines.append("Latest:")
        for r in recent:
            lines.append(f"• {r['reference']} · {clip(r['name'], 22)} · {money(r['total'])} · {r['status']}")
    await safe_edit(call.message, "\n".join(lines), kb([[("⬅️  Back", "menu")]]))
    await call.answer()


@router.callback_query(F.data == "link:site")
async def cb_site(call: CallbackQuery) -> None:
    if cfg.STOREFRONT_URL:
        await call.message.answer(f"Storefront: {cfg.STOREFRONT_URL}")
    else:
        await call.message.answer("Set STOREFRONT_URL in the server environment to show the link here.")
    await call.answer()


# ------------------------------------------------------------------- products
def products_list(page: int = 0) -> tuple[str, InlineKeyboardMarkup]:
    products = db.list_products()
    pages = max(1, (len(products) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, pages - 1))
    chunk = products[page * PAGE_SIZE : (page + 1) * PAGE_SIZE]
    rows: list[list[tuple[str, str]]] = []
    for p in chunk:
        flag = "" if p["inStock"] else " · out"
        star = "★ " if p["featured"] else ""
        rows.append([(f"{star}{clip(p['name'], 26)} — {money(p['price'])}{flag}", f"prod:view:{p['slug']}")])
    nav = []
    if pages > 1:
        nav.append(("◀️", f"prod:list:{max(0, page - 1)}"))
        nav.append((f"{page + 1}/{pages}", "noop"))
        nav.append(("▶️", f"prod:list:{min(pages - 1, page + 1)}"))
    rows.append([("➕  New piece", "prod:new")])
    if nav:
        rows.append(nav)
    rows.append([("⬅️  Menu", "menu")])
    text = f"📦  Products ({len(products)})\n\nTap a piece to edit it."
    if not chunk:
        text = "📦  Products\n\nNo pieces yet. Add the first one below."
    return text, kb(rows)


@router.callback_query(F.data == "noop")
async def cb_noop(call: CallbackQuery) -> None:
    await call.answer()


@router.callback_query(F.data.startswith("prod:list:"))
async def cb_products(call: CallbackQuery) -> None:
    page = int(call.data.split(":")[2])
    text, markup = products_list(page)
    await safe_edit(call.message, text, markup)
    await call.answer()


@router.callback_query(F.data.startswith("prod:view:"))
async def cb_product(call: CallbackQuery) -> None:
    slug = call.data.split(":", 2)[2]
    await render_product(call.message, slug)
    await call.answer()


async def render_product(message: Message, slug: str) -> None:
    p = db.get_product(slug)
    if not p:
        await safe_edit(message, "That piece no longer exists.", kb([[("⬅️  Products", "prod:list:0")]]))
        return
    category = next((c["name"] for c in db.list_categories() if c["slug"] == p["categorySlug"]), "—")
    collection_names = ", ".join(p["collectionSlugs"]) or "—"
    text = (
        f"📦  {p['name']}\n"
        f"{p['subtitle'] or '—'}\n\n"
        f"Price: {money(p['price'])}\n"
        f"Volume: {p['volume'] or '—'}\n"
        f"Category: {category}\n"
        f"Collections: {collection_names}\n"
        f"Badge: {p['badge'] or '—'}\n"
        f"Featured: {'yes' if p['featured'] else 'no'}   ·   In stock: {'yes' if p['inStock'] else 'no'}\n"
        f"Photos: {len(p['images'])}\n\n"
        f"{clip(p['description'], 260) or 'No description yet.'}\n\n"
        f"Slug: /{p['slug']}"
    )
    markup = kb(
        [
            [("✏️ Name", f"prod:edit:{slug}:name"), ("💶 Price", f"prod:edit:{slug}:price")],
            [("📝 Subtitle", f"prod:edit:{slug}:subtitle"), ("📐 Volume", f"prod:edit:{slug}:volume")],
            [("📄 Description", f"prod:edit:{slug}:description"), ("🏷 Badge", f"prod:edit:{slug}:badge")],
            [("🗂 Category", f"prod:cat:{slug}"), ("🎨 Collections", f"prod:coll:{slug}")],
            [
                (
                    ("⭐ Featured: on" if p["featured"] else "☆ Featured: off"),
                    f"prod:toggle:{slug}:featured",
                ),
                (
                    ("✅ In stock" if p["inStock"] else "⛔️ Out of stock"),
                    f"prod:toggle:{slug}:in_stock",
                ),
            ],
            [(f"🖼 Photos · {len(p['images'])}", f"prod:img:{slug}")],
            [("🗑 Delete", f"prod:del:{slug}"), ("⬅️ Products", "prod:list:0")],
        ]
    )
    await safe_edit(message, text, markup)


@router.callback_query(F.data.startswith("prod:toggle:"))
async def cb_product_toggle(call: CallbackQuery) -> None:
    _, _, slug, field = call.data.split(":")
    p = db.get_product(slug)
    if p:
        db.set_product_field(slug, field, not p["featured" if field == "featured" else "inStock"])
        await render_product(call.message, slug)
    await call.answer("Updated")


@router.callback_query(F.data.startswith("prod:del:"))
async def cb_product_delete(call: CallbackQuery) -> None:
    parts = call.data.split(":")
    slug = parts[2]
    if len(parts) == 3:
        p = db.get_product(slug)
        if not p:
            await call.answer("Already deleted", show_alert=True)
            return
        await safe_edit(
            call.message,
            f"Delete “{p['name']}”?\n\nThis removes it from the website. Photos stay in /media.",
            kb([[("Yes, delete", f"prod:del:yes:{slug}"), ("Cancel", f"prod:view:{slug}")]]),
        )
        await call.answer()
        return
    db.delete_product(slug)
    text, markup = products_list(0)
    await safe_edit(call.message, "Deleted.\n\n" + text, markup)
    await call.answer("Deleted")


@router.callback_query(F.data.startswith("prod:edit:"))
async def cb_product_edit(call: CallbackQuery, state: FSMContext) -> None:
    _, _, slug, field = call.data.split(":")
    p = db.get_product(slug)
    if not p:
        await call.answer("Not found", show_alert=True)
        return
    labels = {
        "name": ("Name", p["name"], "Send the new name."),
        "subtitle": ("Subtitle", p["subtitle"], "Example: Hand-Blown Crystal · 210 ml"),
        "description": ("Description", p["description"], "Send the catalogue description."),
        "price": ("Price", str(p["price"]), "Send a number, e.g. 42"),
        "volume": ("Volume", p["volume"], "Example: 210 ml or 15 / 30 ml"),
        "badge": ("Badge", p["badge"], "Example: New · Signature · Trade — or “-” to clear."),
    }
    title, current, hint = labels[field]
    await state.set_state(EditText.value)
    await state.update_data(kind="product", slug=slug, field=field)
    await call.message.answer(
        f"✏️ {title}\n\nCurrent: {current or '—'}\n\n{hint}\n\nSend /cancel to abort.",
    )
    await call.answer()


@router.callback_query(F.data.startswith("prod:cat:"))
async def cb_product_category(call: CallbackQuery) -> None:
    slug = call.data.split(":", 2)[2]
    p = db.get_product(slug)
    if not p:
        await call.answer("Not found", show_alert=True)
        return
    rows = [
        [(("✅ " if c["slug"] == p["categorySlug"] else "") + c["name"], f"prod:cat:set:{slug}:{c['slug']}")]
        for c in db.list_categories()
    ]
    rows.append([("⬅️ Back", f"prod:view:{slug}")])
    await safe_edit(call.message, f"🗂 Category for {p['name']}", kb(rows))
    await call.answer()


@router.callback_query(F.data.startswith("prod:cat:set:"))
async def cb_product_category_set(call: CallbackQuery) -> None:
    _, _, _, slug, category = call.data.split(":")
    db.set_product_field(slug, "category_slug", category)
    await render_product(call.message, slug)
    await call.answer("Category updated")


@router.callback_query(F.data.startswith("prod:coll:"))
async def cb_product_collections(call: CallbackQuery) -> None:
    slug = call.data.split(":", 2)[2]
    p = db.get_product(slug)
    if not p:
        await call.answer("Not found", show_alert=True)
        return
    rows = [
        [
            (
                ("✅ " if c["slug"] in p["collectionSlugs"] else "▫️ ") + c["name"],
                f"prod:coll:set:{slug}:{c['slug']}",
            )
        ]
        for c in db.list_collections()
    ]
    rows.append([("⬅️ Back", f"prod:view:{slug}")])
    await safe_edit(
        call.message,
        f"🎨 Collections for {p['name']}\n\nTap to toggle. A piece can sit in several collections.",
        kb(rows),
    )
    await call.answer()


@router.callback_query(F.data.startswith("prod:coll:set:"))
async def cb_product_collections_set(call: CallbackQuery) -> None:
    _, _, _, slug, collection = call.data.split(":")
    p = db.get_product(slug)
    if not p:
        await call.answer("Not found", show_alert=True)
        return
    current = p["collectionSlugs"]
    updated = [c for c in current if c != collection]
    if collection not in current:
        updated.append(collection)
    db.set_product_collections(slug, updated)
    await cb_product_collections(call)


@router.callback_query(F.data.startswith("prod:img:"))
async def cb_product_images(call: CallbackQuery) -> None:
    slug = call.data.split(":", 2)[2]
    p = db.get_product(slug)
    if not p:
        await call.answer("Not found", show_alert=True)
        return
    rows: list[list[tuple[str, str]]] = [[("➕  Upload photo", f"prod:img:add:{slug}")]]
    for index, image in enumerate(p["images"]):
        label = f"{'🖼 Cover' if index == 0 else f'🖼 Photo {index + 1}'} — {image.split('/')[-1][:18]}"
        rows.append([(label, "noop"), ("🗑", f"prod:img:del:{slug}:{index}")])
    rows.append([("⬅️ Back", f"prod:view:{slug}")])
    text = (
        f"🖼 Photos — {p['name']}\n\n"
        f"{len(p['images'])} uploaded. The first photo is the cover on the site.\n\n"
        "Send a photo as an image file (not as a file attachment) to add it."
    )
    await safe_edit(call.message, text, kb(rows))
    await call.answer()


@router.callback_query(F.data.startswith("prod:img:add:"))
async def cb_product_image_add(call: CallbackQuery, state: FSMContext) -> None:
    slug = call.data.split(":", 3)[3]
    await state.set_state(UploadPhoto.photo)
    await state.update_data(kind="product", slug=slug)
    await call.message.answer("📷 Send the photo now (as a photo, compressed is fine). /cancel to abort.")
    await call.answer()


@router.callback_query(F.data.startswith("prod:img:del:"))
async def cb_product_image_delete(call: CallbackQuery) -> None:
    _, _, _, slug, index = call.data.split(":")
    p = db.get_product(slug)
    if p:
        images = p["images"]
        idx = int(index)
        if 0 <= idx < len(images):
            images.pop(idx)
            db.set_product_images(slug, images)
            await call.answer("Photo removed")
        else:
            await call.answer("Already removed")
    await cb_product_images(call)


@router.callback_query(F.data == "prod:new")
async def cb_product_new(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(NewProduct.name)
    await call.message.answer("➕ New piece\n\n1/2 — Send the product name.")
    await call.answer()


# ------------------------------------------------------------------ categories
def categories_text_kb() -> tuple[str, InlineKeyboardMarkup]:
    categories = db.list_categories()
    rows: list[list[tuple[str, str]]] = []
    for c in categories:
        count = sum(1 for p in db.list_products() if p["categorySlug"] == c["slug"])
        rows.append([(f"{clip(c['name'], 22)} · {count}", f"cat:view:{c['slug']}")])
    rows.append([("➕  New category", "cat:new")])
    rows.append([("⬅️  Menu", "menu")])
    return (
        f"🗂  Categories ({len(categories)})\n\nThey appear as filters in the shop and on the home page.",
        kb(rows),
    )


@router.callback_query(F.data == "cat:list")
async def cb_categories(call: CallbackQuery) -> None:
    text, markup = categories_text_kb()
    await safe_edit(call.message, text, markup)
    await call.answer()


@router.callback_query(F.data.startswith("cat:view:"))
async def cb_category_view(call: CallbackQuery) -> None:
    slug = call.data.split(":", 2)[2]
    category = next((c for c in db.list_categories() if c["slug"] == slug), None)
    if not category:
        await call.answer("Not found", show_alert=True)
        return
    await safe_edit(
        call.message,
        f"🗂 {category['name']}\n\nBlurb: {category['blurb'] or '—'}\nSlug: /{category['slug']}",
        kb(
            [
                [("✏️ Name", f"cat:edit:{slug}:name"), ("📝 Blurb", f"cat:edit:{slug}:blurb")],
                [("🗑 Delete", f"cat:del:{slug}")],
                [("⬅️ Categories", "cat:list")],
            ]
        ),
    )
    await call.answer()


@router.callback_query(F.data.startswith("cat:edit:"))
async def cb_category_edit(call: CallbackQuery, state: FSMContext) -> None:
    _, _, slug, field = call.data.split(":")
    await state.set_state(EditText.value)
    await state.update_data(kind="category", slug=slug, field=field)
    await call.message.answer("Send the new value. /cancel to abort.")
    await call.answer()


@router.callback_query(F.data.startswith("cat:del:"))
async def cb_category_delete(call: CallbackQuery) -> None:
    slug = call.data.split(":", 2)[2]
    db.delete_category(slug)
    text, markup = categories_text_kb()
    await safe_edit(call.message, "Deleted. Its pieces are now uncategorised.\n\n" + text, markup)
    await call.answer("Deleted")


@router.callback_query(F.data == "cat:new")
async def cb_category_new(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(NewCategory.name)
    await call.message.answer("🗂 New category\n\nSend the name (e.g. Glassware).")
    await call.answer()


# ----------------------------------------------------------------- collections
def collections_text_kb() -> tuple[str, InlineKeyboardMarkup]:
    collections = db.list_collections()
    rows: list[list[tuple[str, str]]] = []
    for c in collections:
        count = sum(1 for p in db.list_products() if c["slug"] in p["collectionSlugs"])
        rows.append([(f"{clip(c['name'], 20)} · {count}", f"coll:view:{c['slug']}")])
    rows.append([("➕  New collection", "coll:new")])
    rows.append([("⬅️  Menu", "menu")])
    return (
        f"🎨  Collections ({len(collections)})\n\nThe collection tiles on the home page and the collection pages.",
        kb(rows),
    )


@router.callback_query(F.data == "coll:list")
async def cb_collections(call: CallbackQuery) -> None:
    text, markup = collections_text_kb()
    await safe_edit(call.message, text, markup)
    await call.answer()


@router.callback_query(F.data.startswith("coll:view:"))
async def cb_collection_view(call: CallbackQuery) -> None:
    slug = call.data.split(":", 2)[2]
    c = next((x for x in db.list_collections() if x["slug"] == slug), None)
    if not c:
        await call.answer("Not found", show_alert=True)
        return
    await safe_edit(
        call.message,
        f"🎨 {c['name']}\n{c['subtitle'] or '—'}\n\n{clip(c['description'], 300) or 'No description.'}\n\n"
        f"Cover: {c['image'] or 'not set'}",
        kb(
            [
                [("✏️ Name", f"coll:edit:{slug}:name"), ("📝 Subtitle", f"coll:edit:{slug}:subtitle")],
                [("📄 Description", f"coll:edit:{slug}:description")],
                [("🖼 Cover photo", f"coll:img:{slug}")],
                [("🗑 Delete", f"coll:del:{slug}"), ("⬅️ Collections", "coll:list")],
            ]
        ),
    )
    await call.answer()


@router.callback_query(F.data.startswith("coll:edit:"))
async def cb_collection_edit(call: CallbackQuery, state: FSMContext) -> None:
    _, _, slug, field = call.data.split(":")
    await state.set_state(EditText.value)
    await state.update_data(kind="collection", slug=slug, field=field)
    await call.message.answer("Send the new value. /cancel to abort.")
    await call.answer()


@router.callback_query(F.data.startswith("coll:img:"))
async def cb_collection_image(call: CallbackQuery, state: FSMContext) -> None:
    slug = call.data.split(":", 2)[2]
    await state.set_state(UploadPhoto.photo)
    await state.update_data(kind="collection", slug=slug)
    await call.message.answer("🖼 Send the cover photo for this collection.")
    await call.answer()


@router.callback_query(F.data.startswith("coll:del:"))
async def cb_collection_delete(call: CallbackQuery) -> None:
    slug = call.data.split(":", 2)[2]
    db.delete_collection(slug)
    text, markup = collections_text_kb()
    await safe_edit(call.message, "Deleted.\n\n" + text, markup)
    await call.answer("Deleted")


@router.callback_query(F.data == "coll:new")
async def cb_collection_new(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(NewCollection.name)
    await call.message.answer("🎨 New collection\n\nSend the name (e.g. Levitating).")
    await call.answer()


# -------------------------------------------------------------------- settings
SETTING_FIELDS = [
    ("brand", "Brand name", "brand"),
    ("tagline", "Tagline", "tagline"),
    ("announcement", "Announcement bar", "announcement"),
    ("about", "About paragraph", "about"),
    ("priceNote", "Price note", "priceNote"),
    ("requestNote", "Request note", "requestNote"),
    ("shippingNote", "Shipping note", "shippingNote"),
    ("returnsNote", "Returns note", "returnsNote"),
    ("currency", "Currency (EUR/USD/AED)", "currency"),
    ("locale", "Locale (en-AE)", "locale"),
]

CONTACT_FIELDS = [
    ("contacts.email", "Email", "email"),
    ("contacts.phone", "Phone", "phone"),
    ("contacts.instagram", "Instagram URL", "instagram"),
    ("contacts.telegram", "Telegram URL", "telegram"),
    ("contacts.whatsapp", "WhatsApp link", "whatsapp"),
    ("contacts.address", "Address", "address"),
    ("contacts.hours", "Opening hours", "hours"),
]


def settings_kb() -> InlineKeyboardMarkup:
    rows = [[(label, f"set:edit:{key}")] for key, label, _ in SETTING_FIELDS]
    rows.insert(0, [("📇  Contacts", "set:contacts"), ("🖼  Hero slides", "set:hero")])
    rows.append([("👥  Staff access", "set:staff")])
    rows.append([("⬅️  Menu", "menu")])
    return kb(rows)


@router.callback_query(F.data == "set:menu")
async def cb_settings(call: CallbackQuery) -> None:
    s = db.all_settings()
    text = (
        "⚙️  Site & content\n\n"
        f"Brand: {s['brand']}\n"
        f"Tagline: {clip(s['tagline'], 60)}\n"
        f"Announcement: {clip(s['announcement'], 60) or '—'}\n"
        f"Currency: {s['currency']}   ·   Locale: {s['locale']}\n"
        f"Hero slides: {len(s.get('hero') or [])}\n"
        f"Email: {s.get('contacts', {}).get('email') or '—'}\n\n"
        "Tap a field to change it."
    )
    await safe_edit(call.message, text, settings_kb())
    await call.answer()


def staff_text_kb() -> tuple[str, InlineKeyboardMarkup]:
    staff = db.list_staff()
    owners = ", ".join(str(i) for i in cfg.ADMIN_IDS) or "—"
    lines = [
        "👥  Staff access\n",
        f"Owner (always allowed): {owners}",
        f"Password: {'configured ✅' if cfg.ADMIN_PASSWORD else 'not set ⚠️'}",
        f"Session length: {cfg.AUTH_TTL_HOURS} h\n",
    ]
    rows: list[list[tuple[str, str]]] = []
    if staff:
        lines.append("Signed in with the password:")
        for member in staff:
            name = member["full_name"] or member["username"] or str(member["user_id"])
            lines.append(f"• {clip(name, 28)} · {member['user_id']}")
            rows.append([(f"❌ Revoke {clip(name, 22)}", f"set:staff:revoke:{member['user_id']}")])
    else:
        lines.append("Nobody has signed in with the password yet.")
    rows.append([("⬅️ Back", "set:menu")])
    lines.append("\nChange the password in the BotHost variables (ADMIN_PASSWORD).")
    return "\n".join(lines), kb(rows)


@router.callback_query(F.data == "set:staff")
async def cb_settings_staff(call: CallbackQuery) -> None:
    text, markup = staff_text_kb()
    await safe_edit(call.message, text, markup)
    await call.answer()


@router.callback_query(F.data.startswith("set:staff:revoke:"))
async def cb_settings_staff_revoke(call: CallbackQuery) -> None:
    user_id = int(call.data.split(":")[3])
    db.revoke_staff(user_id)
    text, markup = staff_text_kb()
    await safe_edit(call.message, text, markup)
    await call.answer("Access revoked")


@router.callback_query(F.data == "set:contacts")
async def cb_settings_contacts(call: CallbackQuery) -> None:
    contacts = db.get_setting("contacts", {}) or {}
    rows = [[(f"{label}: {clip(str(contacts.get(key, '')), 26) or '—'}", f"set:edit:{path}")] for path, label, key in CONTACT_FIELDS]
    rows.append([("⬅️ Back", "set:menu")])
    await safe_edit(call.message, "📇 Contacts\n\nShown in the footer, on the About page and in the request emails.", kb(rows))
    await call.answer()


@router.callback_query(F.data.startswith("set:edit:"))
async def cb_settings_edit(call: CallbackQuery, state: FSMContext) -> None:
    key = call.data.split(":", 2)[2]
    current: Any = db.get_setting("contacts", {}) if key.startswith("contacts.") else None
    if current is not None:
        current = current.get(key.split(".", 1)[1], "")
    else:
        current = db.get_setting(key, "")
    if isinstance(current, (list, dict)):
        current = ""
    await state.set_state(EditText.value)
    await state.update_data(kind="setting", field=key)
    await call.message.answer(
        f"⚙️ {key}\n\nCurrent: {clip(str(current), 400) or '—'}\n\nSend the new value. /cancel to abort."
    )
    await call.answer()


def hero_kb(slides: list[dict]) -> InlineKeyboardMarkup:
    rows: list[list[tuple[str, str]]] = []
    for index, slide in enumerate(slides):
        title = slide.get("title") or slide.get("productSlug") or f"Slide {index + 1}"
        rows.append([(f"{index + 1}. {clip(title, 28)}", f"set:hero:slide:{index}")])
    rows.append([("➕  Add slide", "set:hero:add"), ("🗑  Remove last", "set:hero:del")])
    rows.append([("⬅️ Back", "set:menu")])
    return kb(rows)


@router.callback_query(F.data == "set:hero")
async def cb_hero(call: CallbackQuery) -> None:
    slides = db.get_setting("hero", []) or []
    text = (
        "🖼  Hero slides\n\n"
        "The big rotating block on the home page. Each slide shows one piece, a huge headline and a short copy line.\n\n"
        f"Slides: {len(slides)}"
    )
    await safe_edit(call.message, text, hero_kb(slides))
    await call.answer()


@router.callback_query(F.data.startswith("set:hero:slide:"))
async def cb_hero_slide(call: CallbackQuery) -> None:
    index = int(call.data.split(":")[3])
    slides = db.get_setting("hero", []) or []
    if not (0 <= index < len(slides)):
        await call.answer("Slide not found", show_alert=True)
        return
    slide = slides[index]
    text = (
        f"🖼 Slide {index + 1}\n\n"
        f"Piece: {slide.get('productSlug') or '—'}\n"
        f"Kicker: {slide.get('kicker') or '—'}\n"
        f"Headline: {slide.get('title') or '—'}\n"
        f"Name: {slide.get('name') or '—'}\n"
        f"Subtitle: {slide.get('subtitle') or '—'}\n"
        f"Copy: {clip(slide.get('copy', ''), 200) or '—'}"
    )
    await safe_edit(
        call.message,
        text,
        kb(
            [
                [("📦 Choose piece", f"set:hero:pick:{index}")],
                [("Kicker", f"set:hero:field:{index}:kicker"), ("Headline", f"set:hero:field:{index}:title")],
                [("Name", f"set:hero:field:{index}:name"), ("Subtitle", f"set:hero:field:{index}:subtitle")],
                [("Copy line", f"set:hero:field:{index}:copy")],
                [("⬅️ Slides", "set:hero")],
            ]
        ),
    )
    await call.answer()


@router.callback_query(F.data.startswith("set:hero:pick:"))
async def cb_hero_pick(call: CallbackQuery) -> None:
    index = int(call.data.split(":")[3])
    products = db.list_products()
    rows = [[(clip(p["name"], 32), f"set:hero:set:{index}:{p['slug']}")] for p in products[:24]]
    rows.append([("⬅️ Back", f"set:hero:slide:{index}")])
    await safe_edit(call.message, "📦 Which piece should this slide show?", kb(rows))
    await call.answer()


@router.callback_query(F.data.startswith("set:hero:set:"))
async def cb_hero_set(call: CallbackQuery) -> None:
    _, _, _, index_raw, slug = call.data.split(":")
    index = int(index_raw)
    slides = db.get_setting("hero", []) or []
    product = db.get_product(slug)
    if not (0 <= index < len(slides)) or not product:
        await call.answer("Not found", show_alert=True)
        return
    slides[index].update(
        {
            "productSlug": slug,
            "name": product["name"],
            "subtitle": product["subtitle"] or "The collection",
            "copy": slides[index].get("copy") or product["description"][:150],
        }
    )
    db.set_setting("hero", slides)
    await cb_hero_slide(call)


@router.callback_query(F.data.startswith("set:hero:field:"))
async def cb_hero_field(call: CallbackQuery, state: FSMContext) -> None:
    _, _, _, index_raw, field = call.data.split(":")
    await state.set_state(EditText.value)
    await state.update_data(kind="hero", index=int(index_raw), field=field)
    await call.message.answer(f"Send the new {field}. /cancel to abort.")
    await call.answer()


@router.callback_query(F.data == "set:hero:add")
async def cb_hero_add(call: CallbackQuery) -> None:
    slides = db.get_setting("hero", []) or []
    products = db.list_products()
    if not products:
        await call.answer("Add a product first", show_alert=True)
        return
    product = products[len(slides) % len(products)]
    slides.append(
        {
            "productSlug": product["slug"],
            "kicker": "The collection",
            "title": product["name"].split(" ")[0],
            "name": product["name"],
            "subtitle": product["subtitle"] or "",
            "copy": product["description"][:160],
        }
    )
    db.set_setting("hero", slides)
    await cb_hero(call)


@router.callback_query(F.data == "set:hero:del")
async def cb_hero_delete(call: CallbackQuery) -> None:
    slides = db.get_setting("hero", []) or []
    if slides:
        slides.pop()
        db.set_setting("hero", slides)
    await cb_hero(call)


# -------------------------------------------------------------------- requests
STATUS_LABELS = {"new": "🆕 new", "processing": "🚚 in progress", "done": "✅ done", "cancelled": "🗑 cancelled"}


def requests_text_kb(status: str = "new", page: int = 0) -> tuple[str, InlineKeyboardMarkup]:
    counts = db.request_counts()
    requests = db.list_requests(status, limit=100)
    pages = max(1, (len(requests) + 4) // 5)
    page = max(0, min(page, pages - 1))
    chunk = requests[page * 5 : (page + 1) * 5]
    rows: list[list[tuple[str, str]]] = []
    for r in chunk:
        rows.append(
            [
                (
                    f"{r['reference']} · {clip(r['name'], 18)} · {money(r['total'])}",
                    f"req:view:{r['id']}",
                )
            ]
        )
    if page > 0 or page < pages - 1:
        nav = []
        if page > 0:
            nav.append(("◀️", f"req:list:{status}:{page - 1}"))
        nav.append((f"{page + 1}/{pages}", "noop"))
        if page < pages - 1:
            nav.append(("▶️", f"req:list:{status}:{page + 1}"))
        rows.append(nav)
    rows.append(
        [
            ("🆕 New", "req:list:new:0"),
            ("🚚 Progress", "req:list:processing:0"),
            ("✅ Done", "req:list:done:0"),
        ]
    )
    rows.append([("📚 All", "req:list:all:0"), ("⬅️ Menu", "menu")])
    text = (
        "🧾  Requests\n\n"
        f"New: {counts['new']}  ·  In progress: {counts['processing']}  ·  Done: {counts['done']}\n\n"
        f"Showing: {status}"
    )
    return text, kb(rows)


def request_detail(r: dict) -> tuple[str, InlineKeyboardMarkup]:
    lines = [f"🧾  {r['reference']}   ·   {STATUS_LABELS.get(r['status'], r['status'])}", "", f"👤 {r['name']}"]
    if r["company"]:
        lines.append(f"🏢 {r['company']}")
    lines.append(f"✉️ {r['email']}")
    if r["phone"]:
        lines.append(f"📞 {r['phone']}")
    if r["country"]:
        lines.append(f"🌍 {r['country']}")
    lines.append(f"🕒 {r['createdAt']}")
    lines.append("")
    lines.append("Items:")
    for item in r["items"]:
        lines.append(f"  {item.get('qty', 1)} × {item.get('name', item.get('slug'))} — {money(float(item.get('sum', 0)))}")
    lines.append("")
    lines.append(f"Total: {money(r['total'])} {r['currency']}")
    if r["note"]:
        lines.append("")
        lines.append(f"Note: {r['note']}")
    rows = [
        [("✅ Mark done", f"req:status:{r['id']}:done"), ("🚚 In progress", f"req:status:{r['id']}:processing")],
        [("✉️ Reply by email", f"req:mail:{r['id']}"), ("🗑 Cancel", f"req:status:{r['id']}:cancelled")],
        [("⬅️ Requests", "req:list:new:0")],
    ]
    return "\n".join(lines), kb(rows)


@router.callback_query(F.data.startswith("req:list:"))
async def cb_requests(call: CallbackQuery) -> None:
    _, _, status, page = call.data.split(":")
    text, markup = requests_text_kb(status, int(page))
    await safe_edit(call.message, text, markup)
    await call.answer()


@router.callback_query(F.data.startswith("req:view:"))
async def cb_request_view(call: CallbackQuery) -> None:
    request_id = int(call.data.split(":")[2])
    r = db.get_request(request_id)
    if not r:
        await call.answer("Not found", show_alert=True)
        return
    text, markup = request_detail(r)
    await safe_edit(call.message, text, markup)
    await call.answer()


@router.callback_query(F.data.startswith("req:status:"))
async def cb_request_status(call: CallbackQuery) -> None:
    _, _, request_id, status = call.data.split(":")
    db.set_request_status(int(request_id), status)
    r = db.get_request(int(request_id))
    if r:
        text, markup = request_detail(r)
        await safe_edit(call.message, text, markup)
    await call.answer(f"Marked {status}")


@router.callback_query(F.data.startswith("req:mail:"))
async def cb_request_mail(call: CallbackQuery) -> None:
    request_id = int(call.data.split(":")[2])
    r = db.get_request(request_id)
    if r:
        await call.message.answer(
            f"Reply to {r['email']} about {r['reference']}.\nSubject: Your Cocktail Embassy request {r['reference']}"
        )
    await call.answer()


# ------------------------------------------------------------------- password
@router.message(AskPassword.password, F.text)
async def handle_password(message: Message, state: FSMContext) -> None:
    import hmac

    raw = (message.text or "").strip()
    await state.clear()
    if not cfg.ADMIN_PASSWORD:
        await message.answer("No password is configured on the server. Set ADMIN_PASSWORD in BotHost.")
        return
    if not hmac.compare_digest(raw.encode(), cfg.ADMIN_PASSWORD.encode()):
        await message.answer("❌ Wrong password. Try again with /login.")
        return
    db.grant_staff(
        message.from_user.id,
        username=message.from_user.username or "",
        full_name=message.from_user.full_name or "",
    )
    await message.answer(
        "✅ Access granted. You stay signed in for "
        f"{cfg.AUTH_TTL_HOURS} hours. Send /logout to end the session.",
    )
    await show_main_menu(message, state)


# ------------------------------------------------------------- text input FSM
@router.message(EditText.value, F.text)
async def handle_edit_text(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    kind = data.get("kind")
    field = data.get("field")
    raw = (message.text or "").strip()
    await state.clear()

    if kind == "product":
        slug = data["slug"]
        p = db.get_product(slug)
        if not p:
            await message.answer("Piece not found.", reply_markup=main_menu_kb())
            return
        if field == "price":
            try:
                value = float(raw.replace(",", ".").replace("€", "").strip())
            except ValueError:
                await message.answer("Price must be a number, e.g. 42")
                return
            db.set_product_field(slug, "price", value)
        elif field == "badge" and raw in {"-", "—", "none", "clear"}:
            db.set_product_field(slug, "badge", "")
        else:
            db.set_product_field(slug, field, raw)
        await render_product(message, slug)
        return

    if kind == "category":
        slug = data["slug"]
        category = next((c for c in db.list_categories() if c["slug"] == slug), None)
        if category:
            db.upsert_category(
                slug=slug,
                name=raw if field == "name" else category["name"],
                blurb=raw if field == "blurb" else category["blurb"],
                sort=category["sort"],
            )
        text, markup = categories_text_kb()
        await message.answer("Saved.\n\n" + text, reply_markup=markup)
        return

    if kind == "collection":
        slug = data["slug"]
        collection = next((c for c in db.list_collections() if c["slug"] == slug), None)
        if collection:
            payload = dict(collection)
            payload[field] = raw
            db.upsert_collection(
                slug=slug,
                name=payload["name"],
                subtitle=payload["subtitle"],
                description=payload["description"],
                image=payload["image"],
                sort=payload["sort"],
            )
        text, markup = collections_text_kb()
        await message.answer("Saved.\n\n" + text, reply_markup=markup)
        return

    if kind == "setting":
        if field == "currency":
            raw = raw.upper()[:3]
            if not raw.isalpha():
                await message.answer("Currency must be a three-letter code, e.g. EUR.")
                return
        if field.startswith("contacts."):
            key = field.split(".", 1)[1]
            contacts = db.get_setting("contacts", {}) or {}
            contacts[key] = raw
            db.set_setting("contacts", contacts)
        else:
            db.set_setting(field, raw)
        await message.answer("Saved.\n\n" + _settings_summary(), reply_markup=settings_kb())
        return

    if kind == "hero":
        index = int(data["index"])
        slides = db.get_setting("hero", []) or []
        if 0 <= index < len(slides):
            slides[index][field] = raw
            db.set_setting("hero", slides)
        await message.answer("Saved.\n\nHero slides updated.", reply_markup=hero_kb(slides))
        return

    await message.answer("Nothing to update.", reply_markup=main_menu_kb())


def _settings_summary() -> str:
    s = db.all_settings()
    return (
        "⚙️  Site & content\n\n"
        f"Brand: {s['brand']}\n"
        f"Tagline: {clip(s['tagline'], 60)}\n"
        f"Announcement: {clip(s['announcement'], 60) or '—'}\n"
        f"Currency: {s['currency']}   ·   Locale: {s['locale']}"
    )


@router.message(NewCategory.name, F.text)
async def handle_new_category(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    await state.clear()
    if not name:
        await message.answer("Send a name.")
        return
    db.upsert_category(slug=db.unique_slug("categories", db.slugify(name)), name=name, sort=db.next_sort("category"))
    text, markup = categories_text_kb()
    await message.answer(f"Category “{name}” created.\n\n" + text, reply_markup=markup)


@router.message(NewCollection.name, F.text)
async def handle_new_collection(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    await state.clear()
    if not name:
        await message.answer("Send a name.")
        return
    db.upsert_collection(slug=db.unique_slug("collections", db.slugify(name)), name=name, sort=db.next_sort("collection"))
    text, markup = collections_text_kb()
    await message.answer(f"Collection “{name}” created.\n\n" + text, reply_markup=markup)


@router.message(NewProduct.name, F.text)
async def handle_new_product_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Send a name.")
        return
    await state.update_data(name=name)
    await state.set_state(NewProduct.price)
    await message.answer(f"“{name}”\n\n2/2 — Send the price in {db.get_setting('currency', 'EUR')} (e.g. 42).")


@router.message(NewProduct.price, F.text)
async def handle_new_product_price(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    try:
        price = float(raw.replace(",", ".").replace("€", "").strip())
    except ValueError:
        await message.answer("Price must be a number, e.g. 42")
        return
    data = await state.get_data()
    await state.clear()
    categories = db.list_categories()
    slug = db.unique_slug("products", db.slugify(data.get("name", "piece")))
    db.upsert_product(
        slug=slug,
        name=data.get("name", "New piece"),
        price=price,
        category_slug=categories[0]["slug"] if categories else "",
        sort=db.next_sort("product"),
    )
    await message.answer(
        "Created. Now add photos, a description and a category.",
        reply_markup=kb([[("Open piece", f"prod:view:{slug}")], [("All products", "prod:list:0")]]),
    )


# ------------------------------------------------------------------ photo FSM
@router.message(UploadPhoto.photo, F.photo)
async def handle_photo(message: Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    kind = data.get("kind")
    slug = data.get("slug")
    await state.clear()

    file_id = message.photo[-1].file_id
    cfg.MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex[:12]}.jpg"
    target = cfg.MEDIA_DIR / filename
    await bot.download(file_id, destination=target)
    url = f"/media/{filename}"

    if kind == "product":
        p = db.get_product(slug)
        if not p:
            await message.answer("Piece not found.")
            return
        images = list(p["images"])
        if message.caption and message.caption.strip().lower() in {"cover", "first"}:
            images.insert(0, url)
        else:
            images.append(url)
        db.set_product_images(slug, images)
        await message.answer(f"Photo added ({len(images)} total).")
        await render_product(message, slug)
        return

    if kind == "collection":
        collection = next((c for c in db.list_collections() if c["slug"] == slug), None)
        if collection:
            db.upsert_collection(
                slug=slug,
                name=collection["name"],
                subtitle=collection["subtitle"],
                description=collection["description"],
                image=url,
                sort=collection["sort"],
            )
        await message.answer("Cover updated.")
        text, markup = collections_text_kb()
        await message.answer(text, reply_markup=markup)
        return


@router.message(UploadPhoto.photo)
async def handle_photo_wrong_type(message: Message) -> None:
    await message.answer("Please send an actual photo (not a file). /cancel to abort.")


@router.message()
async def fallback(message: Message) -> None:
    await message.answer("Use the menu below.", reply_markup=main_menu_kb())


# ------------------------------------------------------------------ lifecycle
_bot: Bot | None = None
_dp: Dispatcher | None = None


def get_bot() -> Bot:
    global _bot
    if _bot is None:
        if not cfg.BOT_TOKEN:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")
        _bot = Bot(token=cfg.BOT_TOKEN)
    return _bot


def get_dispatcher() -> Dispatcher:
    global _dp
    if _dp is None:
        _dp = Dispatcher(storage=MemoryStorage())
        _dp.message.middleware(AdminOnly())
        _dp.callback_query.middleware(AdminOnly())
        _dp.include_router(router)
    return _dp


async def run_polling() -> None:
    while True:
        try:
            bot = get_bot()
            dp = get_dispatcher()
            await bot.delete_webhook(drop_pending_updates=False)
            log.info("Bot polling started")
            await dp.start_polling(bot, handle_signals=False, allowed_updates=dp.resolve_used_update_types())
            return
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            log.error("Bot polling crashed: %s — restarting in 10s", exc)
            await asyncio.sleep(10)


async def notify_new_request(record: dict) -> None:
    if not (cfg.ADMIN_IDS or db.list_staff()) or not cfg.BOT_TOKEN:
        return
    bot = get_bot()
    text, markup = request_detail(record)
    header = "🔔  New request from the website\n\n"
    recipients = list(dict.fromkeys(list(cfg.ADMIN_IDS) + [s["user_id"] for s in db.list_staff()]))
    for chat_id in recipients:
        try:
            await bot.send_message(chat_id, header + text, reply_markup=markup)
        except Exception as exc:  # noqa: BLE001
            log.warning("Could not notify %s: %s", chat_id, exc)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    db.init_db()
    asyncio.run(run_polling())
