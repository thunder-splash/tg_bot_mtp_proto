from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import func, select

from mtproto.secret import mask_secret

from ..config import get_settings
from ..db import session_scope
from ..keyboards import admin_kb, delivery_kb, main_menu
from ..models import Order, OrderStatus, ProxyNode, SlotMode, Subscription
from ..services.catalog import (
    active_sub_count,
    add_node_from_url,
    list_nodes,
    refresh_node_health,
)
from ..services.orders import get_order, mark_paid, provision_order
from ..states import AdminStates
from .. import texts

log = logging.getLogger(__name__)
router = Router(name="admin")


def _is_admin(user_id: int) -> bool:
    return user_id in get_settings().admin_id_set


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer(texts.admin_help(), reply_markup=admin_kb())


@router.callback_query(F.data == "admin:add")
@router.message(Command("addproxy"))
async def admin_add_start(event: Message | CallbackQuery, state: FSMContext) -> None:
    uid = event.from_user.id
    if not _is_admin(uid):
        return
    await state.set_state(AdminStates.waiting_proxy_url)
    text = (
        "Пришлите ссылку:\n"
        "<code>https://t.me/proxy?server=…&port=…&secret=…</code>\n"
        "или <code>tg://proxy?…</code>\n\n"
        "Опционально первой строкой mode: <code>shared</code> или <code>dedicated</code>."
    )
    if isinstance(event, CallbackQuery):
        await event.message.answer(text)
        await event.answer()
    else:
        await event.answer(text)


@router.message(AdminStates.waiting_proxy_url)
async def admin_add_url(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id):
        return
    raw = (message.text or "").strip()
    mode = SlotMode.shared
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    if lines and lines[0].lower() in {"shared", "dedicated"}:
        mode = SlotMode(lines[0].lower())
        url = "\n".join(lines[1:]).strip() or (lines[1] if len(lines) > 1 else "")
    else:
        url = raw

    try:
        async with session_scope() as session:
            node = await add_node_from_url(session, url, mode=mode)
            status = await refresh_node_health(session, node)
            nid = node.id
            host = f"{node.host}:{node.port}"
            key_masked = mask_secret(node.key_hex)
        await state.clear()
        await message.answer(
            f"Нода <b>#{nid}</b> добавлена · {mode.value}\n"
            f"<code>{host}</code>\n"
            f"Ключ: <code>{key_masked}</code>\n"
            f"TCP: <b>{status.value}</b>",
            reply_markup=admin_kb(),
        )
    except ValueError as e:
        await message.answer(f"Не разобрал ссылку: {e}")
    except Exception:
        log.exception("add proxy failed")
        await message.answer("Ошибка сохранения. Проверьте ссылку.")


@router.callback_query(F.data == "admin:nodes")
@router.message(Command("nodes"))
async def admin_nodes(event: Message | CallbackQuery) -> None:
    if not _is_admin(event.from_user.id):
        return
    async with session_scope() as session:
        nodes = await list_nodes(session)
        lines: list[str] = []
        for n in nodes:
            used = await active_sub_count(session, n.id)
            flag = "on" if n.enabled else "off"
            lines.append(
                f"#{n.id} [{flag}] {n.mode.value} {n.status.value} "
                f"{n.host}:{n.port} · {used}/{n.max_subscribers} · {mask_secret(n.key_hex)}"
            )
        text = "◈ <b>Ноды</b>\n\n" + ("\n".join(lines) if lines else "Пусто. /addproxy")
    if isinstance(event, CallbackQuery):
        await event.message.answer(text, reply_markup=admin_kb())
        await event.answer()
    else:
        await event.answer(text, reply_markup=admin_kb())


@router.callback_query(F.data == "admin:stats")
@router.message(Command("stats"))
async def admin_stats(event: Message | CallbackQuery) -> None:
    if not _is_admin(event.from_user.id):
        return
    async with session_scope() as session:
        orders = await session.scalar(select(func.count()).select_from(Order)) or 0
        paid = await session.scalar(
            select(func.count()).select_from(Order).where(
                Order.status.in_(
                    [OrderStatus.paid, OrderStatus.provisioned, OrderStatus.active]
                )
            )
        ) or 0
        revenue = await session.scalar(
            select(func.coalesce(func.sum(Order.amount_rub), 0)).where(
                Order.status.in_(
                    [OrderStatus.paid, OrderStatus.provisioned, OrderStatus.active]
                )
            )
        ) or 0
        nodes = await session.scalar(select(func.count()).select_from(ProxyNode)) or 0
        subs = await session.scalar(select(func.count()).select_from(Subscription)) or 0
        text = (
            "◈ <b>Статистика</b>\n\n"
            f"Заказов: {orders}\n"
            f"Оплаченных: {paid}\n"
            f"Выручка (учёт): {revenue} ₽\n"
            f"Нод: {nodes}\n"
            f"Подписок: {subs}"
        )
    if isinstance(event, CallbackQuery):
        await event.message.answer(text, reply_markup=admin_kb())
        await event.answer()
    else:
        await event.answer(text, reply_markup=admin_kb())


@router.message(Command("credit"))
async def admin_credit(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return
    parts = (message.text or "").split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Использование: /credit &lt;order_id&gt;")
        return
    order_id = int(parts[1])
    async with session_scope() as session:
        order = await get_order(session, order_id)
        if not order:
            await message.answer("Заказ не найден")
            return
        await mark_paid(session, order, provider="manual", payment_id=f"manual:{order_id}")
        try:
            sub = await provision_order(session, order)
        except RuntimeError:
            await message.answer("Оплачено, но нет свободных слотов. /addproxy")
            return
        buyer_tg = order.user.tg_id
        delivery = texts.delivery(sub)
        kb = delivery_kb(sub)

    await message.answer(f"Заказ #{order_id} зачислен и выдан.", reply_markup=admin_kb())
    try:
        await message.bot.send_message(buyer_tg, delivery, reply_markup=kb)
    except Exception:
        log.warning("failed to deliver to buyer %s", buyer_tg)
        await message.answer("Не удалось написать покупателю — пусть откроет «Мои прокси».")


@router.message(Command("checknodes"))
async def admin_check_nodes(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return
    async with session_scope() as session:
        nodes = await list_nodes(session)
        lines = []
        for n in nodes:
            st = await refresh_node_health(session, n)
            lines.append(f"#{n.id} {n.host}:{n.port} → {st.value}")
    await message.answer("Проверка:\n" + "\n".join(lines) if lines else "Нет нод")
