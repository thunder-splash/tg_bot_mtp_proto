from __future__ import annotations

import asyncio
import socket
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mtproto import build_link, parse_proxy_url

from ..models import NodeStatus, ProxyNode, SlotMode, Subscription


async def add_node_from_url(
    session: AsyncSession,
    url: str,
    *,
    label: str = "",
    mode: SlotMode = SlotMode.shared,
    max_subscribers: int = 100,
    notes: str | None = None,
) -> ProxyNode:
    ep = parse_proxy_url(url)
    node = ProxyNode(
        label=label or f"{ep.host}:{ep.port}",
        host=ep.host,
        port=ep.port,
        secret_hex=ep.secret.client_hex,
        key_hex=ep.mtproxybot_secret,
        tls_domain=ep.secret.domain,
        mode=mode,
        status=NodeStatus.unknown,
        enabled=True,
        max_subscribers=max_subscribers if mode is SlotMode.shared else 1,
        notes=notes,
    )
    session.add(node)
    await session.flush()
    return node


def node_tg_link(node: ProxyNode) -> str:
    return build_link(node.host, node.port, node.secret_hex, scheme="tg")


def node_https_link(node: ProxyNode) -> str:
    return build_link(node.host, node.port, node.secret_hex, scheme="https")


async def tcp_alive(host: str, port: int, timeout: float = 3.0) -> bool:
    def _check() -> bool:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            return False

    return await asyncio.to_thread(_check)


async def refresh_node_health(session: AsyncSession, node: ProxyNode) -> NodeStatus:
    ok = await tcp_alive(node.host, node.port)
    node.status = NodeStatus.alive if ok else NodeStatus.dead
    node.last_checked_at = datetime.now(timezone.utc)
    await session.flush()
    return node.status


async def active_sub_count(session: AsyncSession, node_id: int) -> int:
    now = datetime.now(timezone.utc)
    q = (
        select(func.count())
        .select_from(Subscription)
        .where(
            Subscription.node_id == node_id,
            Subscription.revoked.is_(False),
            Subscription.ends_at > now,
        )
    )
    return int(await session.scalar(q) or 0)


async def pick_available_node(session: AsyncSession) -> ProxyNode | None:
    """Prefer shared alive nodes with free capacity; fall back to dedicated unused."""
    now = datetime.now(timezone.utc)
    result = await session.scalars(
        select(ProxyNode).where(ProxyNode.enabled.is_(True)).order_by(ProxyNode.id)
    )
    nodes = list(result)
    # Prefer known-alive, then unknown, skip dead
    nodes.sort(key=lambda n: (0 if n.status is NodeStatus.alive else 1 if n.status is NodeStatus.unknown else 2, n.id))

    for node in nodes:
        if node.status is NodeStatus.dead:
            continue
        if node.mode is SlotMode.dedicated:
            used = await active_sub_count(session, node.id)
            if used == 0:
                return node
            continue
        used = await active_sub_count(session, node.id)
        if used < node.max_subscribers:
            return node
    # Ignore "now" unused warning
    _ = now
    return None


async def list_nodes(session: AsyncSession) -> list[ProxyNode]:
    result = await session.scalars(select(ProxyNode).order_by(ProxyNode.id))
    return list(result)
