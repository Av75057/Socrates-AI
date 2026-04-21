# Публичные диалоги и шеринг

## Публичная ссылка

- Авторизованный пользователь в **истории диалогов** или на странице диалога нажимает **«Опубликовать»**.
- API: `POST /users/me/conversations/{id}/publish` возвращает `share_url`, `preview_card_url` (HTML с Open Graph для соцсетей).
- Просмотр: фронтенд `GET /share/{slug}` (страница без входа), данные: `GET /public/share/{slug}`.
- Снятие: `DELETE /users/me/conversations/{id}/unpublish`.

В **`.env` бэкенда** задайте `PUBLIC_SITE_URL=https://ваш-фронт` — тогда в ответах и в OG будет корректный абсолютный URL. В dev можно не задавать (по умолчанию `http://localhost:5173`).

## Превью в соцсетях

- `GET /public/share/{slug}/card` — HTML с мета-тегами `og:*`, редирект на SPA `/share/{slug}`.
- `GET /public/share/{slug}/og.png` — картинка превью (Pillow).

Боты соцсетей обычно заходят по **полному URL API** на `/public/share/.../card`; в посте пользователь может вставить ссылку на **фронт** `/share/{slug}` — превью зависит от того, какую ссылку сохранили.

## Шеринг достижений и навыков (клиент)

- Компонент `ShareModal`: генерация PNG через **html2canvas**, кнопки **react-share** (Twitter, Facebook, Telegram, WhatsApp, LinkedIn), Web Share API на мобильных.
- Достижения: модалка достижений → «Поделиться».
- Навыки: страница **Навыки** → «Поделиться прогрессом».

## Новые соцсети

В `frontend/src/components/sharing/ShareModal.jsx` добавьте кнопку из [react-share](https://github.com/nygardk/react-share#readme) (импорт иконки + `*ShareButton` с `url` и при необходимости `title`).
