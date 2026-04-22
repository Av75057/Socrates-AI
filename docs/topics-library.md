# Библиотека тем

## Что это

Раздел `/topics` показывает готовые темы для диалогов. У темы есть:

- `title`
- `description`
- `initial_prompt`
- `difficulty`
- `tags`
- `is_premium`

При запуске темы создаётся новый `conversation`, а первое сообщение тьютора берётся из `initial_prompt`.

## Как добавить тему через UI

1. Открой `/admin/topics`.
2. Заполни `title`, `description`, `initial_prompt`, `difficulty`, `tags`.
3. При необходимости включи `Premium`.
4. Нажми `Создать тему`.

Для редактирования выбери тему в таблице, после чего форма справа заполнится текущими значениями.

## AI-генерация темы

На странице `/admin/topics` есть блок `Генерация через AI`.

Он вызывает `POST /admin/topics/generate` и возвращает черновик:

- `title`
- `description`
- `initial_prompt`
- `difficulty`
- `tags`

Черновик не сохраняется автоматически: админ или educator может поправить поля и только потом нажать `Создать тему`.

## API

Публичные endpoints:

- `GET /topics`
- `GET /topics/{id}`
- `GET /topics/tags`
- `POST /topics/{id}/start`

Управление темами:

- `GET /admin/topics`
- `POST /admin/topics`
- `PUT /admin/topics/{id}`
- `DELETE /admin/topics/{id}`
- `POST /admin/topics/generate`

## Premium-доступ

Если тема помечена как `is_premium=true`, запуск разрешён только пользователям с активным Pro-планом (`pro`, `yearly`, `team`).

Для free-пользователя backend возвращает `402 Payment Required`.

## Кэш

Список тем и список тегов кэшируются в Redis на 5 минут. После создания, редактирования, удаления или старта темы кэш инвалидируется.
