const botUser = (import.meta.env.VITE_BOT_USERNAME || "").replace(/^@/, "");
const price1 = import.meta.env.VITE_PRICE_1M || "299";
const price3 = import.meta.env.VITE_PRICE_3M || "799";
const price12 = import.meta.env.VITE_PRICE_12M || "2490";

const botUrl = botUser
  ? `https://t.me/${botUser}?start=site`
  : "https://t.me/";

export default function App() {
  return (
    <main className="page">
      <header className="hero">
        <div>
          <p className="eyebrow">Traffic Mtproto</p>
          <h1>Прокси в один тап</h1>
          <p className="lead">
            Пока человек подключён по вашей ссылке, публичный канал может стоять
            первой строкой его чатов. Не баннер в ленте — место над перепиской.
          </p>
          <div className="actions">
            <a className="cta" href={botUrl}>
              Купить в Telegram
            </a>
            <a className="cta ghost" href="#how">
              Как это работает
            </a>
          </div>
          {!botUser ? (
            <p className="note">
              Задайте <code>VITE_BOT_USERNAME</code> при сборке, чтобы кнопка вела
              в вашего бота.
            </p>
          ) : null}
        </div>
        <aside className="price-card">
          <span>Личный доступ</span>
          <strong>от {price1} ₽ / мес</strong>
        </aside>
      </header>

      <section className="grid" id="how">
        <article className="card">
          <h3>Один тап</h3>
          <p>
            Ссылка <code>tg://proxy</code> — подтвердили в Telegram, и трафик уже
            через ваш адрес. Без VPN-приложений.
          </p>
        </article>
        <article className="card">
          <h3>Канал над чатами</h3>
          <p>
            Официальный спонсор MTProto через @MTProxybot. Пока прокси включён —
            канал наверху у тех, кто ещё не подписан.
          </p>
        </article>
        <article className="card">
          <h3>Живые ноды</h3>
          <p>
            Выдаём только рабочие endpoints. Оплата в боте — Crypto Pay или
            вручную через админа.
          </p>
        </article>
      </section>

      <section className="card">
        <h3>Тарифы</h3>
        <p>Выбор и оплата — только в боте. Сайт ничего не «выпускает».</p>
        <div className="plans">
          <div className="plan">
            <div className="label">1 месяц</div>
            <div className="sum">{price1} ₽</div>
          </div>
          <div className="plan">
            <div className="label">3 месяца</div>
            <div className="sum">{price3} ₽</div>
          </div>
          <div className="plan">
            <div className="label">12 месяцев</div>
            <div className="sum">{price12} ₽</div>
          </div>
        </div>
        <div className="actions">
          <a className="cta" href={botUrl}>
            Открыть бота
          </a>
        </div>
      </section>

      <section className="faq" style={{ marginTop: "2rem" }}>
        <h2 style={{ marginBottom: "1rem" }}>FAQ</h2>
        <details>
          <summary>Это VPN?</summary>
          <p>
            Нет. MTProto-прокси работает только внутри Telegram: обход блокировок
            мессенджера и опциональный канал-спонсор.
          </p>
        </details>
        <details>
          <summary>Где получить ссылку?</summary>
          <p>
            После оплаты бот пришлёт кнопку «Подключить». На сайте прокси не
            генерируются.
          </p>
        </details>
        <details>
          <summary>Как повесить свой канал?</summary>
          <p>
            Бот пришлёт шаги для @MTProxybot. Нужен публичный канал; проверка —
            со второго аккаунта без подписки.
          </p>
        </details>
      </section>

      <footer className="footer">
        Traffic Mtproto · продажи только через Telegram-бота · не храните токены
        на фронте
      </footer>
    </main>
  );
}
