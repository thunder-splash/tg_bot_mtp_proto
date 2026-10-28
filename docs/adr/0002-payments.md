# ADR 0002: Payments v1

## Status

Accepted

## Decision

- **Crypto Pay (CryptoBot)** for self-serve crypto invoices in RUB fiat amount.
- **Admin `/credit <order_id>`** for bank transfer / cash / Stars-later.
- Stars / Telegram Payments — phase 2.

## Consequences

Shop works without Crypto Pay token (manual credit only). Invoice IDs stored on `orders.payment_id`; never log API tokens.
