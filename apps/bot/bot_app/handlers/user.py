from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ..config import Settings, get_settings
from ..db import session_scope
from ..keyboards import (
    delivery_kb,
    main_menu,
    mine_kb,
    pay_kb,
    plans_kb,
    skip_channel_kb,
)
from ..models import OrderStatus
from ..services.crypto_pay import CryptoPayClient, CryptoPayError
from ..services.orders import (
    create_order,
    get_or_create_user,
    get_order,
    mark_paid,
    normalize_channel,
    provision_order,
    user_subscriptions,
)
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from ..models import Subscription as SubModel
from ..states import BuyStates
from .. import texts

log = logging.getLogger(__name__)
router = Router(name="user")


def _crypto(settings: Settings) -> CryptoPayClient:
    return CryptoPayClient(settings.crypto_pay_token)


@router.message(CommandStart())
@router.message(Command("menu"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    settings = get_settings()
    async with session_scope() as session:
        await get_or_create_user(
            session,
            message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
        )
    await message.answer(texts.welcome(settings), reply_markup=main_menu(settings))


@router.callback_query(F.data == "home")
async def cb_home(cq: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    settings = get_settings()
    await cq.message.answer(texts.welcome(settings), reply_markup=main_menu(settings))
    await cq.answer()


@router.callback_query(F.data == "how")
async def cb_how(cq: CallbackQuery) -> None:
    settings = get_settings()
    await cq.message.answer(texts.how_it_works(), reply_markup=main_menu(settings))
    await cq.answer()


@router.callback_query(F.data == "buy")
async def cb_buy(cq: CallbackQuery, state: FSMContext) -> None:
    settings = get_settings()
    await state.set_state(BuyStates.choosing_plan)
    await cq.message.answer(texts.plans(settings), reply_markup=plans_kb(settings))
    await cq.answer()


@router.callback_query(F.data.startswith("plan:"))
async def cb_plan(cq: CallbackQuery, state: FSMContext) -> None:
    months = int(cq.data.split(":")[1])
    await state.update_data(months=months)
    await state.set_state(BuyStates.waiting_channel)
    await cq.message.answer(texts.ask_channel(), reply_markup=skip_channel_kb())
    await cq.answer()


@router.callback_query(F.data == "channel_skip", BuyStates.waiting_channel)
async def cb_channel_skip(cq: CallbackQuery, state: FSMContext) -> None:
    await _place_order(cq.message, state, channel=None, tg_user=cq.from_user)
    await cq.answer()


@router.message(BuyStates.waiting_channel, Command("skip"))
async def msg_channel_skip(message: Message, state: FSMContext) -> None:
    await _place_order(message, state, channel=None, tg_user=message.from_user)


@router.message(BuyStates.waiting_channel)
async def msg_channel(message: Message, state: FSMContext) -> None:
    ch = normalize_channel(message.text or "")
    if not ch:
        await message.answer("Нужен публичный канал: @name или t.me/name. Или /skip.")
        return
    await _place_order(message, state, channel=ch, tg_user=message.from_user)


async def _place_order(message: Message, state: FSMContext, *, channel: str | None, tg_user) -> None:
    settings = get_settings()
    data = await state.get_data()
    months = int(data.get("months") or 1)
    await state.clear()

    async with session_scope() as session:
        user = await get_or_create_user(
            session,
            tg_user.id,
            username=tg_user.username,
            full_name=tg_user.full_name,
        )
        order = await create_order(session, user, months, settings, channel=channel)
        order_id = order.id
        amount = order.amount_rub

    crypto = _crypto(settings)
    pay_url = None
    if crypto.enabled:
        try:
            inv = await crypto.create_invoice(
                amount_rub=amount,
                description=f"MTProto {months}m #{order_id}",
                payload=f"order:{order_id}",
            )
            pay_url = inv.get("bot_invoice_url") or inv.get("pay_url")
            invoice_id = str(inv.get("invoice_id") or inv.get("id") or "")
            async with session_scope() as session:
                order = await get_order(session, order_id)
                if order:
                    order.payment_id = invoice_id
                    order.payment_provider = "crypto_pay"
        except CryptoPayError as e:
            log.warning("crypto invoice failed: %s", e)

    await message.answer(
        texts.payment_msg(order_id, amount, months),
        reply_markup=pay_kb(order_id, pay_url=pay_url, crypto_enabled=crypto.enabled),
    )
    # Notify admins
    for admin_id in settings.admin_id_set:
        try:
            await message.bot.send_message(
                admin_id,
                f"Новый заказ #{order_id} на {amount} ₽ ({months} мес). /credit {order_id}",
            )
        except Exception:
            log.debug("admin notify failed", exc_info=True)


@router.callback_query(F.data.startswith("checkpay:"))
async def cb_check_pay(cq: CallbackQuery) -> None:
    settings = get_settings()
    order_id = int(cq.data.split(":")[1])
    crypto = _crypto(settings)
    if not crypto.enabled:
        await cq.answer("Crypto Pay не настроен — ждите /credit от админа", show_alert=True)
        return

    async with session_scope() as session:
        order = await get_order(session, order_id)
        if not order or order.user.tg_id != cq.from_user.id:
            await cq.answer("Заказ не найден", show_alert=True)
            return
        if order.status in {OrderStatus.active, OrderStatus.paid, OrderStatus.provisioned}:
            sub = await session.scalar(
                select(SubModel).where(
                    SubModel.order_id == order.id, SubModel.revoked.is_(False)
                )
            )
            if not sub:
                try:
                    sub = await provision_order(session, order)
                except RuntimeError:
                    await cq.message.answer(texts.no_capacity())
                    await cq.answer()
                    return
            await cq.message.answer(texts.delivery(sub), reply_markup=delivery_kb(sub))
            await cq.answer("Уже оплачен")
            return

        if not order.payment_id:
            await cq.answer("Счёт не создан", show_alert=True)
            return

        try:
            items = await crypto.get_invoices([int(order.payment_id)])
        except (CryptoPayError, ValueError) as e:
            log.warning("get_invoices: %s", e)
            await cq.answer("Не удалось проверить", show_alert=True)
            return

        paid = any(i.get("status") == "paid" for i in items)
        if not paid:
            await cq.answer("Пока не оплачено", show_alert=True)
            return

        await mark_paid(session, order, provider="crypto_pay", payment_id=order.payment_id)
        try:
            sub = await provision_order(session, order)
        except RuntimeError:
            await cq.message.answer(texts.no_capacity())
            for admin_id in settings.admin_id_set:
                try:
                    await cq.bot.send_message(
                        admin_id, f"Заказ #{order_id} оплачен, но нет слотов!"
                    )
                except Exception:
                    pass
            await cq.answer()
            return

        await cq.message.answer(texts.delivery(sub), reply_markup=delivery_kb(sub))
        await cq.answer("Оплата получена")


@router.callback_query(F.data == "mine")
async def cb_mine(cq: CallbackQuery) -> None:
    settings = get_settings()
    async with session_scope() as session:
        user = await get_or_create_user(session, cq.from_user.id)
        subs = await user_subscriptions(session, user.id)
        if not subs:
            await cq.message.answer("◈ Пока пусто. Купите доступ — ссылка появится здесь.", reply_markup=main_menu(settings))
            await cq.answer()
            return
        lines = [texts.sub_card(s) for s in subs]
        # detach nodes for keyboard after session
        await cq.message.answer(
            "◈ <b>Ваши прокси</b>\n\n" + "\n\n".join(lines),
            reply_markup=mine_kb(subs),
        )
    await cq.answer()


@router.callback_query(F.data.startswith("guide:"))
async def cb_guide(cq: CallbackQuery) -> None:
    sub_id = int(cq.data.split(":")[1])
    settings = get_settings()
    async with session_scope() as session:
        user = await get_or_create_user(session, cq.from_user.id)
        sub = await session.scalar(
            select(SubModel)
            .where(SubModel.id == sub_id)
            .options(selectinload(SubModel.node))
        )
        if not sub or sub.user_id != user.id:
            await cq.answer("Не найдено", show_alert=True)
            return
        node = sub.node
        text = texts.sponsor_guide(node, sub.channel)
    await cq.message.answer(text, reply_markup=main_menu(settings))
    await cq.answer()


@router.callback_query(F.data == "sponsor")
async def cb_sponsor(cq: CallbackQuery) -> None:
    settings = get_settings()
    async with session_scope() as session:
        user = await get_or_create_user(session, cq.from_user.id)
        subs = await user_subscriptions(session, user.id)
        last = subs[0] if subs else None
        node = last.node if last else None
        channel = last.channel if last else None
        text = texts.sponsor_guide(node, channel)
    await cq.message.answer(text, reply_markup=main_menu(settings))
    await cq.answer()


@router.callback_query(F.data.startswith("renew:"))
async def cb_renew(cq: CallbackQuery, state: FSMContext) -> None:
    sub_id = int(cq.data.split(":")[1])
    async with session_scope() as session:
        user = await get_or_create_user(session, cq.from_user.id)
        sub = await session.scalar(select(SubModel).where(SubModel.id == sub_id))
        channel = sub.channel if sub and sub.user_id == user.id else None
    await state.update_data(renew_channel=channel)
    settings = get_settings()
    await state.set_state(BuyStates.choosing_plan)
    await cq.message.answer(texts.plans(settings), reply_markup=plans_kb(settings))
    await cq.answer()
