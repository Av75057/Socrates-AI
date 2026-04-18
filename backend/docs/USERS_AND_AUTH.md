# Пользователи, БД и админка

## Миграции

```bash
cd backend
# SQLite по умолчанию (файл ./socrates.db)
.venv/bin/alembic upgrade head
```

Для PostgreSQL задайте в `.env`:

```
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/socrates
```

Затем снова `alembic upgrade head`.

## Переменные окружения

См. `backend/.env.example` (создайте `.env` рядом с `app/`).

- `DATABASE_URL` — строка SQLAlchemy.
- `JWT_SECRET` — длинная случайная строка для продакшена.
- `JWT_ALGORITHM` — по умолчанию `HS256`.
- `ACCESS_TOKEN_EXPIRE_MINUTES` — срок access-токена (по умолчанию 1440).

## Первый администратор

Новый пользователь с ролью `admin`:

```bash
cd backend
.venv/bin/python scripts/create_admin.py admin@example.com ВашПароль123 --name Админ
```

Уже зарегистрировались как обычный пользователь — выдать роль `admin` по email:

```bash
cd backend
.venv/bin/python scripts/create_admin.py --promote ваш@email.ru
```

Опционально сменить пароль при повышении: добавьте новый пароль вторым аргументом после `--promote … email …`.

После `--promote` обновите сессию во фронте (выход и вход или жёсткое обновление страницы), чтобы подтянулась роль.

## Архитектура данных

- **Гость**: по-прежнему Redis/memory для `session_id`, памяти и педагогики.
- **Авторизованный пользователь**:
  - Долгосрочная память чата: ключ Redis/memory — `str(user.id)`.
  - Диалоги и сообщения: таблицы `conversations`, `messages`. У диалога есть `session_key` (UUID), совпадающий с `session_id` на фронте для Redis-состояния тьютора.
  - Запрос `POST /chat` с заголовком `Authorization: Bearer …` и телом `conversation_id` + `session_id == session_key` сохраняет пары сообщений в БД.
  - Геймификация: Redis по `session_id`; при `POST /gamification/action` с тем же Bearer состояние дублируется в `gamification_progress`.
  - Режим тьютора из `user_settings.tutor_mode` подмешивается в педагогическое состояние перед ходом.

## CORS

Список origin задаётся `CORS_ORIGINS` в `.env` (через запятую). Для продакшена ограничьте домен фронта.
