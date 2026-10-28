# ADR 0001: Stack and delivery model

## Status

Accepted

## Context

The Grok demo issued synthetic IPs and skipped payment. We need a real shop: sell working MTProto links, optionally promote a public channel via `@MTProxybot`.

## Decision

1. **Bot-first shop** — aiogram 3 + SQLite; landing is CTA-only.
2. **Hybrid catalog** — admin pastes real `t.me/proxy` links now; later telemt nodes provision per-user secrets.
3. **Payments** — Crypto Pay (CryptoBot) + admin manual credit; Stars later.
4. **Node software** — telemt (FakeTLS + `user_ad_tags`). Avoid mtg v2 when sponsor channel is required.
5. **No fake fleet** — never generate random public IPs as product.

## Consequences

- Launch without owning VPS (paste customer’s working link).
- Margin improves when we run own NL/DE/FI VPS with telemt.
- Secrets stay in env + DB; agents follow `.cursor/rules/secrets.mdc`.
