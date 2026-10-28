from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class OrderStatus(str, enum.Enum):
    draft = "draft"
    awaiting_payment = "awaiting_payment"
    paid = "paid"
    provisioned = "provisioned"
    active = "active"
    expired = "expired"
    revoked = "revoked"
    cancelled = "cancelled"


class SlotMode(str, enum.Enum):
    shared = "shared"
    dedicated = "dedicated"


class NodeStatus(str, enum.Enum):
    alive = "alive"
    dead = "dead"
    unknown = "unknown"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    orders: Mapped[list[Order]] = relationship(back_populates="user")
    subscriptions: Mapped[list[Subscription]] = relationship(back_populates="user")


class ProxyNode(Base):
    """A real MTProto endpoint (admin-pasted or telemt-managed)."""

    __tablename__ = "proxy_nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    label: Mapped[str] = mapped_column(String(128), default="")
    host: Mapped[str] = mapped_column(String(255))
    port: Mapped[int] = mapped_column(Integer)
    # Full client secret hex (ee… or dd… or plain)
    secret_hex: Mapped[str] = mapped_column(Text)
    # 32-hex key for @MTProxybot
    key_hex: Mapped[str] = mapped_column(String(32))
    tls_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mode: Mapped[SlotMode] = mapped_column(
        Enum(SlotMode, native_enum=False), default=SlotMode.shared
    )
    status: Mapped[NodeStatus] = mapped_column(
        Enum(NodeStatus, native_enum=False), default=NodeStatus.unknown
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    max_subscribers: Mapped[int] = mapped_column(Integer, default=100)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    subscriptions: Mapped[list[Subscription]] = relationship(back_populates="node")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, native_enum=False), default=OrderStatus.draft
    )
    months: Mapped[int] = mapped_column(Integer, default=1)
    amount_rub: Mapped[int] = mapped_column(Integer, default=0)
    channel: Mapped[str | None] = mapped_column(String(128), nullable=True)
    payment_provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    payment_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="orders")
    subscription: Mapped[Subscription | None] = relationship(back_populates="order", uselist=False)


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (UniqueConstraint("order_id", name="uq_sub_order"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    node_id: Mapped[int] = mapped_column(ForeignKey("proxy_nodes.id"), index=True)
    channel: Mapped[str | None] = mapped_column(String(128), nullable=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    delivered_link: Mapped[str] = mapped_column(Text, default="")

    user: Mapped[User] = relationship(back_populates="subscriptions")
    order: Mapped[Order] = relationship(back_populates="subscription")
    node: Mapped[ProxyNode] = relationship(back_populates="subscriptions")
