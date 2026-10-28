# Telemt node

1. `mkdir -p config && cp config.example.toml config/config.toml`
2. Replace `shop` secret with `openssl rand -hex 16`
3. Set `tls_domain` to a popular HTTPS host
4. `docker compose up -d`
5. Register with [@MTProxybot](https://t.me/MTProxybot) — see [docs/mtproxybot.md](../../docs/mtproxybot.md)
6. Paste the working `tg://proxy` / `t.me/proxy` link into the shop bot via `/addproxy`

If `ghcr.io/telemt/telemt:latest` is unavailable, build from [telemt/telemt](https://github.com/telemt/telemt) and set `image:` / `build:` accordingly.
