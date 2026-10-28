from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class SecretKind(str, Enum):
    PLAIN = "plain"
    DD = "dd"
    EE = "ee"


_HEX = re.compile(r"^[0-9a-fA-F]+$")


@dataclass(frozen=True)
class ParsedSecret:
    kind: SecretKind
    key_hex: str
    domain: str | None = None
    raw_hex: str = ""

    @property
    def client_hex(self) -> str:
        """Full secret as used in tg://proxy (hex form)."""
        if self.kind is SecretKind.PLAIN:
            return self.key_hex
        if self.kind is SecretKind.DD:
            return f"dd{self.key_hex}"
        domain_hex = "".join(f"{ord(c):02x}" for c in (self.domain or ""))
        return f"ee{self.key_hex}{domain_hex}"


def mask_secret(secret: str, keep: int = 4) -> str:
    s = (secret or "").strip()
    if len(s) <= keep + 2:
        return "****"
    return f"{s[:2]}****{s[-keep:]}"


def domain_to_hex(domain: str) -> str:
    return "".join(f"{ord(c):02x}" for c in domain)


def hex_to_domain(hex_str: str) -> str:
    if len(hex_str) % 2:
        raise ValueError("domain hex length must be even")
    try:
        return bytes.fromhex(hex_str).decode("ascii")
    except (ValueError, UnicodeDecodeError) as e:
        raise ValueError("invalid domain hex") from e


def parse_secret(secret: str) -> ParsedSecret:
    """Parse plain / dd / ee hex secret (not base64)."""
    raw = (secret or "").strip()
    if not raw:
        raise ValueError("empty secret")
    if not _HEX.match(raw):
        raise ValueError("secret must be hex")
    low = raw.lower()

    if low.startswith("ee"):
        body = low[2:]
        if len(body) < 32:
            raise ValueError("ee secret too short")
        key = body[:32]
        domain_hex = body[32:]
        domain = hex_to_domain(domain_hex) if domain_hex else None
        if not domain:
            raise ValueError("ee secret requires domain")
        return ParsedSecret(SecretKind.EE, key, domain, low)

    if low.startswith("dd"):
        body = low[2:]
        if len(body) != 32:
            raise ValueError("dd secret must be dd + 32 hex")
        return ParsedSecret(SecretKind.DD, body, None, low)

    if len(low) != 32:
        raise ValueError("plain secret must be 32 hex chars")
    return ParsedSecret(SecretKind.PLAIN, low, None, low)


def build_ee_secret(key_hex: str, domain: str) -> str:
    key = key_hex.strip().lower()
    if len(key) != 32 or not _HEX.match(key):
        raise ValueError("key must be 32 hex chars")
    if not domain:
        raise ValueError("domain required")
    return f"ee{key}{domain_to_hex(domain)}"
