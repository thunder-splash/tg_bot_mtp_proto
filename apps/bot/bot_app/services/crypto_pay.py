from __future__ import annotations

from typing import Any

import aiohttp

from mtproto.secret import mask_secret


CRYPTO_PAY_API = "https://pay.crypt.bot/api"


class CryptoPayError(Exception):
    pass


class CryptoPayClient:
    def __init__(self, token: str) -> None:
        self._token = token.strip()

    @property
    def enabled(self) -> bool:
        return bool(self._token)

    def _headers(self) -> dict[str, str]:
        return {"Crypto-Pay-API-Token": self._token}

    async def _call(self, method: str, payload: dict[str, Any] | None = None) -> Any:
        if not self.enabled:
            raise CryptoPayError("CRYPTO_PAY_TOKEN not set")
        url = f"{CRYPTO_PAY_API}/{method}"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload or {}, headers=self._headers()) as resp:
                data = await resp.json(content_type=None)
        if not data.get("ok"):
            err = data.get("error", {})
            # Never include token in message
            raise CryptoPayError(str(err.get("name") or err or "crypto_pay_failed"))
        return data.get("result")

    async def create_invoice(
        self,
        *,
        amount_rub: int,
        description: str,
        payload: str,
        paid_btn_url: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "currency_type": "fiat",
            "fiat": "RUB",
            "amount": str(amount_rub),
            "description": description[:1024],
            "payload": payload[:4096],
            "expires_in": 3600,
            "allow_comments": False,
            "allow_anonymous": True,
        }
        if paid_btn_url:
            body["paid_btn_name"] = "callback"
            body["paid_btn_url"] = paid_btn_url
        return await self._call("createInvoice", body)

    async def get_invoices(self, invoice_ids: list[int]) -> list[dict[str, Any]]:
        result = await self._call("getInvoices", {"invoice_ids": ",".join(map(str, invoice_ids))})
        if isinstance(result, dict) and "items" in result:
            return list(result["items"])
        if isinstance(result, list):
            return result
        return []


def safe_invoice_log(invoice: dict[str, Any]) -> str:
    inv_id = invoice.get("invoice_id") or invoice.get("id")
    status = invoice.get("status")
    return f"invoice={inv_id} status={status} hash={mask_secret(str(invoice.get('hash') or ''), 4)}"
