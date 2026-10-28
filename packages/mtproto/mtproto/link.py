from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qs, unquote, urlparse

from .secret import ParsedSecret, parse_secret


@dataclass(frozen=True)
class ProxyEndpoint:
    host: str
    port: int
    secret: ParsedSecret

    @property
    def tg_link(self) -> str:
        return build_link(self.host, self.port, self.secret.client_hex, scheme="tg")

    @property
    def https_link(self) -> str:
        return build_link(self.host, self.port, self.secret.client_hex, scheme="https")

    @property
    def mtproxybot_secret(self) -> str:
        """32-hex key only — what @MTProxybot expects."""
        return self.secret.key_hex


def build_link(host: str, port: int, secret_hex: str, scheme: str = "tg") -> str:
    host = host.strip()
    secret_hex = secret_hex.strip()
    if scheme == "https":
        return f"https://t.me/proxy?server={host}&port={port}&secret={secret_hex}"
    return f"tg://proxy?server={host}&port={port}&secret={secret_hex}"


def parse_proxy_url(url: str) -> ProxyEndpoint:
    """Parse tg://proxy?... or https://t.me/proxy?..."""
    raw = (url or "").strip()
    if not raw:
        raise ValueError("empty url")

    # Allow bare query pasted after "proxy?"
    if raw.startswith("server="):
        raw = "tg://proxy?" + raw

    parsed = urlparse(raw)
    qs = parse_qs(parsed.query)

    # Some clients paste without scheme
    if not qs and "proxy?" in raw:
        qs = parse_qs(raw.split("proxy?", 1)[1])

    def first(name: str) -> str:
        vals = qs.get(name) or []
        return unquote(vals[0]).strip() if vals else ""

    host = first("server")
    port_s = first("port")
    secret_s = first("secret")
    if not host or not port_s or not secret_s:
        raise ValueError("url must include server, port, secret")
    try:
        port = int(port_s)
    except ValueError as e:
        raise ValueError("invalid port") from e
    if not (1 <= port <= 65535):
        raise ValueError("port out of range")

    secret = parse_secret(secret_s)
    return ProxyEndpoint(host=host, port=port, secret=secret)
