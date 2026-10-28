# Дешёвые источники под MTProto-ноды

Публичные списки чужих прокси **не использовать** как товар: общие секреты, нестабильны, нельзя повесить свой канал-спонсор.

Нужен свой VPS: **1 vCPU / ~1 ГБ RAM / порт 443**, софт — **telemt** (см. `infra/telemt`).

## Бюджетные VPS (ориентир 2026)

| Провайдер | Регион | Ориентир цены | Заметки |
|-----------|--------|---------------|---------|
| [FirstByte](https://firstbyte.ru/) | MSK | от ~129 ₽ | Дёшево; RU DPI жёстче |
| [VDSina](https://vdsina.ru/) / [Macloud](https://macloud.ru/) | MSK | ~150 ₽ | Карты РФ |
| [Xorek](https://xorek.cloud/) | DE promo | ~149 ₽ | EU дешевле для обхода |
| [1cent.host](https://1cent.host/) | NL/DE/FI | ~180 ₽ | Promo-тарифы |
| [HOSTKEY](https://hostkey.com/) vm.pico | EU | ~€2.5 | Много локаций |
| [Hetzner](https://www.hetzner.com/cloud/) CX23 | EU | ~€5.5 | Стабильнее при росте |

**Старт:** 1–2 ноды в **NL / DE / FI**. Бот + SQLite можно на том же микро-VPS.

## Софт ноды

1. **telemt** — FakeTLS (`ee`) + `ad_tag` / `user_ad_tags` → канал над чатами. Рекомендуем.
2. Официальный [MTProxy](https://github.com/TelegramMessenger/MTProxy) — запасной путь под `-P` / ad_tag.
3. **mtg v2** — только если сознательно продаёте доступ **без** спонсор-канала (ad_tag вырезан).

## Каталог в боте (без своих VPS)

Админ: `/addproxy` и вставка рабочей ссылки вида:

`https://t.me/proxy?server=…&port=…&secret=ee…`

Секрет **не коммитить**. Первую ноду можно взять у заказчика через админку.
