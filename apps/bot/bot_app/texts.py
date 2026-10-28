from __future__ import annotations

from datetime import datetime, timezone

from mtproto.secret import mask_secret

from .config import Settings
from .models import ProxyNode, Subscription


def welcome(settings: Settings) -> str:
    return (
        "✦ <b>Traffic Mtproto</b>\n\n"
        "Прокси в один тап. Открыли ссылку — Telegram уже идёт через ваш адрес. "
        "Без приложений и настроек.\n\n"
        "Пока человек подключён, <b>ваш публичный канал может стоять первой строкой чатов</b> "
        "(спонсор прокси через @MTProxybot).\n\n"
        f"✦ Личный доступ · от <b>{settings.price_1m} ₽</b> / мес"
    )


def how_it_works() -> str:
    return (
        "◎ <b>Как это работает</b>\n\n"
        "1. Выбираете срок и оплачиваете.\n"
        "2. Получаете кнопку «Подключить» — одна ссылка <code>tg://proxy</code>.\n"
        "3. (Опционально) привязываете публичный канал через @MTProxybot — "
        "канал появится над чатами у тех, кто ещё не подписан.\n\n"
        "Это не VPN: работает только внутри Telegram."
    )


def plans(settings: Settings) -> str:
    return (
        "✦ <b>Выберите срок</b>\n\n"
        f"1 мес — <b>{settings.price_1m} ₽</b>\n"
        f"3 мес — <b>{settings.price_3m} ₽</b>\n"
        f"12 мес — <b>{settings.price_12m} ₽</b>"
    )


def ask_channel() -> str:
    return (
        "✧ Пришлите публичный канал для подсказки в инструкции "
        "(можно пропустить — /skip).\n\n"
        "<code>@name</code> или <code>https://t.me/name</code>"
    )


def payment_msg(order_id: int, amount: int, months: int) -> str:
    return (
        f"✦ Заказ <b>#{order_id}</b>\n"
        f"Срок: <b>{months}</b> мес · <b>{amount} ₽</b>\n\n"
        "Оплатите через Crypto Pay или дождитесь подтверждения админа."
    )


def delivery(sub: Subscription) -> str:
    days = max(0, (sub.ends_at.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)).days)
    channel = sub.channel or "—"
    return (
        "✦ <b>Прокси готов</b>\n\n"
        f"Канал в инструкции: <b>{channel}</b>\n"
        f"Активен ещё ~<b>{days}</b> дн.\n\n"
        "Нажмите «Подключить» ниже. Затем при желании привяжите канал-спонсор."
    )


def sub_card(sub: Subscription) -> str:
    now = datetime.now(timezone.utc)
    ends = sub.ends_at if sub.ends_at.tzinfo else sub.ends_at.replace(tzinfo=timezone.utc)
    days = max(0, (ends - now).days)
    status = "отозван" if sub.revoked else ("активен" if ends > now else "истёк")
    node = sub.node
    host = f"{node.host}:{node.port}" if node else "—"
    return (
        f"◈ <b>#{sub.id}</b> · {status}\n"
        f"Канал: <b>{sub.channel or '—'}</b>\n"
        f"Хост: <code>{host}</code>\n"
        f"До: <code>{ends.date().isoformat()}</code> (~{days} дн.)\n"
        f"Секрет (@MTProxybot): <code>{mask_secret(node.key_hex if node else '', 4)}</code>"
    )


def sponsor_guide(node: ProxyNode | None, channel: str | None) -> str:
    host = f"{node.host}:{node.port}" if node else "IP:PORT"
    secret = node.key_hex if node else "32 hex из карточки"
    ch = channel or "@yourchannel"
    ch_link = f"https://t.me/{ch.lstrip('@')}" if ch.startswith("@") else ch
    return (
        "✧ <b>Канал-спонсор через @MTProxybot</b>\n\n"
        "1. Откройте @MTProxybot → <code>/newproxy</code>\n"
        f"2. Хост и порт: <code>{host}</code>\n"
        f"3. Секрет ровно 32 hex (без ee и домена):\n<code>{secret}</code>\n"
        "4. Возьмите <b>только tag</b> из ответа. Ссылку бота не открывайте.\n"
        "5. В конфиге ноды: <code>use_middle_proxy = true</code> и <code>ad_tag</code>.\n"
        "6. /myproxies → Set promotion → публичная ссылка:\n"
        f"<code>{ch_link}</code>\n"
        "7. Ждите до часа. Проверка — с аккаунта без подписки на канал.\n\n"
        "Если нода shared и не ваша — спонсора настраивает админ магазина."
    )


def admin_help() -> str:
    return (
        "◈ <b>Админ</b>\n\n"
        "/admin — меню\n"
        "/addproxy — вставить t.me/proxy или tg://proxy ссылку\n"
        "/nodes — список нод\n"
        "/credit &lt;order_id&gt; — зачислить оплату вручную\n"
        "/stats — кратко по заказам"
    )


def no_capacity() -> str:
    return (
        "Сейчас нет свободных слотов. Админ уже уведомлён — напишите в поддержку "
        "или попробуйте позже."
    )
