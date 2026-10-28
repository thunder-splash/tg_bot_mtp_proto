from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..config import Settings
from ..models import Order, OrderStatus, Subscription, User
from .catalog import node_tg_link, pick_available_node


CHANNEL_RE = re.compile(r"^@[\w\d_]{4,}$", re.I)
TME_RE = re.compile(r"(?:https?://)?t\.me/([\w\d_]{4,})", re.I)


def normalize_channel(raw: str) -> str | None:
    t = (raw or "").strip()
    m = TME_RE.search(t)
    if m:
        return f"@{m.group(1)}"
    if CHANNEL_RE.match(t):
        return t if t.startswith("@") else f"@{t}"
    if t.startswith("@") and CHANNEL_RE.match(t):
        return t
    return None


async def get_or_create_user(
    session: AsyncSession,
    tg_id: int,
    *,
    username: str | None = None,
    full_name: str | None = None,
) -> User:
    user = await session.scalar(select(User).where(User.tg_id == tg_id))
    if user:
        if username is not None:
            user.username = username
        if full_name is not None:
            user.full_name = full_name
        return user
    user = User(tg_id=tg_id, username=username, full_name=full_name)
    session.add(user)
    await session.flush()
    return user


async def create_order(
    session: AsyncSession,
    user: User,
    months: int,
    settings: Settings,
    channel: str | None = None,
) -> Order:
    amount = settings.price_for_months(months)
    order = Order(
        user_id=user.id,
        status=OrderStatus.awaiting_payment,
        months=months,
        amount_rub=amount,
        channel=channel,
    )
    session.add(order)
    await session.flush()
    return order


async def mark_paid(
    session: AsyncSession,
    order: Order,
    *,
    provider: str,
    payment_id: str | None = None,
) -> Order:
    if order.status in {OrderStatus.paid, OrderStatus.provisioned, OrderStatus.active}:
        return order
    if order.status not in {OrderStatus.awaiting_payment, OrderStatus.draft}:
        raise ValueError(f"cannot pay order in status {order.status}")
    order.status = OrderStatus.paid
    order.payment_provider = provider
    order.payment_id = payment_id
    order.paid_at = datetime.now(timezone.utc)
    await session.flush()
    return order


async def provision_order(session: AsyncSession, order: Order) -> Subscription:
    """Assign a catalog node and create subscription. Idempotent if already provisioned."""
    existing = await session.scalar(
        select(Subscription).where(
            Subscription.order_id == order.id,
            Subscription.revoked.is_(False),
        )
    )
    if existing:
        return existing

    node = await pick_available_node(session)
    if not node:
        raise RuntimeError("NO_CAPACITY")

    now = datetime.now(timezone.utc)
    ends = now + timedelta(days=30 * order.months)
    link = node_tg_link(node)
    sub = Subscription(
        user_id=order.user_id,
        order_id=order.id,
        node_id=node.id,
        channel=order.channel,
        starts_at=now,
        ends_at=ends,
        delivered_link=link,
    )
    session.add(sub)
    order.status = OrderStatus.active
    await session.flush()
    return sub


async def user_subscriptions(session: AsyncSession, user_id: int) -> list[Subscription]:
    result = await session.scalars(
        select(Subscription)
        .where(Subscription.user_id == user_id)
        .options(selectinload(Subscription.node), selectinload(Subscription.order))
        .order_by(Subscription.id.desc())
    )
    return list(result)


async def get_order(session: AsyncSession, order_id: int) -> Order | None:
    return await session.scalar(
        select(Order)
        .where(Order.id == order_id)
        .options(selectinload(Order.subscription), selectinload(Order.user))
    )


async def find_order_by_payment(session: AsyncSession, payment_id: str) -> Order | None:
    return await session.scalar(select(Order).where(Order.payment_id == payment_id))
