from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from .config import Settings
from .models import Subscription


def main_menu(settings: Settings) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="✦ Купить доступ", callback_data="buy")],
        [InlineKeyboardButton(text="◎ Как это работает", callback_data="how")],
        [InlineKeyboardButton(text="◈ Мои прокси", callback_data="mine")],
        [InlineKeyboardButton(text="✧ Спонсор-канал", callback_data="sponsor")],
    ]
    if settings.support_url and settings.support_url != "https://t.me/":
        rows.append([InlineKeyboardButton(text="Поддержка", url=settings.support_url)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def plans_kb(settings: Settings) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"1 мес · {settings.price_1m} ₽", callback_data="plan:1"
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"3 мес · {settings.price_3m} ₽", callback_data="plan:3"
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"12 мес · {settings.price_12m} ₽", callback_data="plan:12"
                )
            ],
            [InlineKeyboardButton(text="← Меню", callback_data="home")],
        ]
    )


def pay_kb(
    order_id: int,
    *,
    pay_url: str | None,
    crypto_enabled: bool,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if pay_url:
        rows.append([InlineKeyboardButton(text="Оплатить Crypto Pay", url=pay_url)])
    if crypto_enabled:
        rows.append(
            [InlineKeyboardButton(text="↻ Проверить оплату", callback_data=f"checkpay:{order_id}")]
        )
    rows.append([InlineKeyboardButton(text="← Меню", callback_data="home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def delivery_kb(sub: Subscription) -> InlineKeyboardMarkup:
    link = sub.delivered_link or (sub.node and f"tg://proxy?server={sub.node.host}&port={sub.node.port}&secret={sub.node.secret_hex}")
    rows: list[list[InlineKeyboardButton]] = []
    if link:
        rows.append([InlineKeyboardButton(text="⚡ Подключить", url=link)])
    rows.append(
        [InlineKeyboardButton(text="✧ Привязать канал", callback_data=f"guide:{sub.id}")]
    )
    rows.append([InlineKeyboardButton(text="← Меню", callback_data="home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def mine_kb(subs: list[Subscription]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for sub in subs[:8]:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"#{sub.id} продлить", callback_data=f"renew:{sub.id}"
                ),
                InlineKeyboardButton(text="гайд", callback_data=f"guide:{sub.id}"),
            ]
        )
    rows.append([InlineKeyboardButton(text="← Меню", callback_data="home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Добавить прокси", callback_data="admin:add")],
            [InlineKeyboardButton(text="Ноды", callback_data="admin:nodes")],
            [InlineKeyboardButton(text="Статистика", callback_data="admin:stats")],
            [InlineKeyboardButton(text="← Меню", callback_data="home")],
        ]
    )


def skip_channel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Пропустить", callback_data="channel_skip")],
            [InlineKeyboardButton(text="Отмена", callback_data="home")],
        ]
    )
