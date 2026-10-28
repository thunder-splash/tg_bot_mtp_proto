from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]
BOT_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(ROOT / ".env", BOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str = Field(alias="BOT_TOKEN", default="")
    admin_ids: str = Field(alias="ADMIN_IDS", default="")
    crypto_pay_token: str = Field(alias="CRYPTO_PAY_TOKEN", default="")
    webhook_url: str = Field(alias="WEBHOOK_URL", default="")
    webhook_secret: str = Field(alias="WEBHOOK_SECRET", default="")
    webhook_path: str = Field(alias="WEBHOOK_PATH", default="/webhook")
    database_url: str = Field(
        alias="DATABASE_URL",
        default=f"sqlite+aiosqlite:///{(BOT_DIR / 'data' / 'shop.db').as_posix()}",
    )
    bot_username: str = Field(alias="BOT_USERNAME", default="")
    price_1m: int = Field(alias="PRICE_1M", default=299)
    price_3m: int = Field(alias="PRICE_3M", default=799)
    price_12m: int = Field(alias="PRICE_12M", default=2490)
    support_url: str = Field(alias="SUPPORT_URL", default="https://t.me/")

    @property
    def admin_id_set(self) -> set[int]:
        out: set[int] = set()
        for part in self.admin_ids.replace(";", ",").split(","):
            part = part.strip()
            if part.isdigit():
                out.add(int(part))
        return out

    def price_for_months(self, months: int) -> int:
        if months == 1:
            return self.price_1m
        if months == 3:
            return self.price_3m
        if months == 12:
            return self.price_12m
        raise ValueError("unsupported plan")


@lru_cache
def get_settings() -> Settings:
    return Settings()
