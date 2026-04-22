# Socrates AI Mobile

Мобильный клиент на Expo + React Native для существующего FastAPI backend.

## Что уже есть в scaffold

- auth: login / register через JWT;
- bottom tabs: chat, history, skills, profile;
- educator tab для ролей `educator` / `admin`;
- chat с offline queue, quick actions, explain panel и auto-save через существующий `/chat`;
- history, conversation detail, skills/progress, settings, pricing;
- read-only public share screen по `slug`;
- profile editing для `full_name`, avatar upload/delete и share card для достижений;
- subscription status через backend endpoint `/users/me/subscription`;
- educator dashboard: classes, students, assignments, student progress;
- SecureStore для токена, AsyncStorage для offline/cache;
- Expo Notifications bootstrap;
- Sentry hook point.

## Запуск

```bash
cd mobile
npm install
npm run start
```

Далее:

- `a` для Android emulator
- `i` для iOS simulator
- или открыть через Expo Go

## Backend URL

По умолчанию используется:

```ts
http://127.0.0.1:8000
```

Для реального устройства поменяйте `expo.extra.apiUrl` в [app.json](./app.json) на IP машины с backend, например:

```json
{
  "expo": {
    "extra": {
      "apiUrl": "http://192.168.1.50:8000"
    }
  }
}
```

## Production notes

- iOS / Android store metadata и signing не настроены в этом scaffold.
- Stripe checkout сейчас идёт через встроенный `WebView` с placeholder URL.
- PDF/email educator reports используют существующий backend.
- Push notifications требуют отдельной настройки Expo project credentials.
- Sentry добавлен как integration point, `dsn` пока пустой.
- Для avatar upload нужен `python-multipart` на backend и установленный `expo-image-picker` в mobile.
- Если backend отдаёт относительный `avatar_url`, mobile клиент достраивает его от `expo.extra.apiUrl`.

## Рекомендуемые следующие шаги

1. Подключить реальные brand assets и splash/icon.
2. Завести backend endpoint для subscription checkout session и webhook Stripe.
3. Добавить deep links на public share screen и purchase success/cancel flow.
4. Прогнать Expo app на iOS/Android и вычистить platform-specific issues.
5. Добавить GitHub Actions / EAS Build pipeline.
