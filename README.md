# Traffic Mtproto — магазин MTProto-прокси

Продакшен-стек: **Telegram-бот** (касса) + **лендинг** (витрина) + шаблон **telemt**-ноды.  
Выдаём только живые ссылки из каталога админа (позже — свои VPS).

Grok-демо в `_vendor_workspace/` — только референс по тону; в прод не запускать.

## Быстрый старт бота

```bash
# из корня репозитория
cp .env.example .env
# заполните BOT_TOKEN и ADMIN_IDS

cd apps/bot
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
# если editable mtproto не встал:
pip install -e ../../packages/mtproto

python -m bot_app.main
```

Админ в Telegram:

1. `/admin`
2. `/addproxy` — вставьте рабочую `https://t.me/proxy?server=…&port=…&secret=…`
3. Покупатель: «Купить» → оплата Crypto Pay **или** вы `/credit <order_id>`

## Лендинг

```bash
cd apps/web
cp .env.example .env
# VITE_BOT_USERNAME=YourBot
npm install
npm run dev
```

Сайт **не** генерирует прокси — только CTA в бота.

## Свои ноды

См. [docs/sources.md](docs/sources.md) и [infra/telemt](infra/telemt).  
Спонсор-канал: [docs/mtproxybot.md](docs/mtproxybot.md).

## Безопасность

- Токены только в `.env` (см. `.cursor/rules/secrets.mdc`)
- Секреты прокси в SQLite, не в git и не на фронте
- Никаких синтетических IP

## Структура

```
apps/bot/          aiogram 3 + SQLite
apps/web/          Vite + React лендинг
packages/mtproto/  парсер ee/dd/plain ссылок
infra/telemt/      Docker Compose шаблон ноды
docs/              ADR, VPS, MTProxybot
.cursor/rules/     правила для агента
```
