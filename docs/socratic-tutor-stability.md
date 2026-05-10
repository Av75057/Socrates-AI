# Стабилизация сократического тьютора

Документ описывает backend-часть стабилизации тьютора: системный промпт, параметры генерации, `tutor_state`, логирование `llm_logs` и точки интеграции в чат.

## Что включено

- Новый prompt-builder: `build_socratic_system_prompt(...)` в [backend/app/services/tutor_prompt.py](/home/andrey/ai-agent/backend/app/services/tutor_prompt.py)
- Параметры генерации в [backend/app/config.py](/home/andrey/ai-agent/backend/app/config.py)
- Состояние тьютора в `conversations.tutor_state`
- Логи всех LLM-вызовов в таблице `llm_logs`
- Сервисы:
  - [backend/app/services/tutor_state_manager.py](/home/andrey/ai-agent/backend/app/services/tutor_state_manager.py)
  - [backend/app/services/llm_logger.py](/home/andrey/ai-agent/backend/app/services/llm_logger.py)

## Как включить и настроить логирование

В `backend/.env`:

```env
LLM_TEMPERATURE=0.3
LLM_TOP_P=0.85
LLM_MAX_TOKENS=250
LLM_PRESENCE_PENALTY=0.2
LLM_FREQUENCY_PENALTY=0.3
LLM_REPEAT_PENALTY=1.1
```

После этого backend будет:
- использовать эти параметры в `OpenRouterProvider` и `OllamaProvider`
- сохранять `system_prompt`, `user_messages`, `model_params`, `raw_response`, `latency_ms` и `response_tokens` в `llm_logs`

## Как смотреть логи

Пример SQL для последних 20 вызовов:

```sql
SELECT
  id,
  conversation_id,
  user_id,
  latency_ms,
  response_tokens,
  created_at,
  substr(raw_response, 1, 200) AS raw_preview
FROM llm_logs
ORDER BY created_at DESC
LIMIT 20;
```

Пример SQL для анализа одного диалога:

```sql
SELECT
  created_at,
  model_params,
  system_prompt,
  user_messages,
  raw_response
FROM llm_logs
WHERE conversation_id = 123
ORDER BY created_at ASC;
```

## Как читать tutor_state

Поле `conversations.tutor_state` хранит:

```json
{
  "level": 2,
  "mode": "friendly",
  "step": 0,
  "stuck": false,
  "last_fallacy": null,
  "topic": "general",
  "attempted_concepts": []
}
```

Обновление происходит на каждом ходе диалога после генерации ответа.

## Как перейти на разделённый pipeline

Обязательная часть ТЗ реализована без выделенного `decision_engine`.

Если понадобится разделить pipeline:

1. Детектор ошибок и глубины оставить в [backend/app/services/fallacy_detector.py](/home/andrey/ai-agent/backend/app/services/fallacy_detector.py)
2. Добавить `decision_engine.py`, который будет принимать:
   - `analysis`
   - `tutor_state`
   - `user_message`
3. На выходе формировать компактный decision payload:
   - `next_question_type`
   - `should_mention_fallacy`
   - `should_offer_hint`
   - `strictness_delta`
4. Подставлять его в `build_socratic_system_prompt(...)` вместо прямого роста логики в route/controller

Это позволит:
- отделить анализ от генерации
- проще дебажить ошибки тьютора
- A/B тестировать prompt и decision layer отдельно
