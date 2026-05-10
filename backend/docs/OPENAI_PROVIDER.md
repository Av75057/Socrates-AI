# OpenAI Provider

`Socrates AI` backend поддерживает `LLM_PROVIDER=openai` без отключения существующих сценариев `openrouter` и `ollama`.

## Как включить OpenAI

В `backend/.env`:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=
OPENAI_API_URL=https://api.openai.com/v1/chat/completions
OPENAI_MODEL_QUESTION=gpt-5.5
OPENAI_MODEL_HINT=gpt-5.4-mini
OPENAI_MODEL_EXPLAIN=gpt-5.5
OPENAI_MODEL_PEDAGOGY=gpt-5.4-mini
OPENAI_MODEL_FALLBACK=gpt-5.4-mini
```

После этого перезапусти backend.

## Какие env переменные нужны

- `LLM_PROVIDER=openai`
- `OPENAI_API_KEY`
- `OPENAI_API_URL`
- `OPENAI_MODEL_QUESTION`
- `OPENAI_MODEL_HINT`
- `OPENAI_MODEL_EXPLAIN`
- `OPENAI_MODEL_PEDAGOGY`
- `OPENAI_MODEL_FALLBACK`

## Модели для MVP

- `OPENAI_MODEL_QUESTION=gpt-5.5`
- `OPENAI_MODEL_HINT=gpt-5.4-mini`
- `OPENAI_MODEL_EXPLAIN=gpt-5.5`
- `OPENAI_MODEL_PEDAGOGY=gpt-5.4-mini`
- `OPENAI_MODEL_FALLBACK=gpt-5.4-mini`

Такой набор оставляет сильную модель на вопросах и объяснениях, а более дешёвую и быструю на hints и педагогике.

## Поведение провайдера

- backend использует `OPENAI_API_KEY` и `OPENAI_API_URL`
- OpenRouter-заголовки `HTTP-Referer` и `X-Title` не отправляются
- streaming остаётся включённым
- fallback остаётся включённым

## Как откатиться

OpenRouter:

```env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=...
```

Ollama:

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b-instruct
```

После смены провайдера перезапусти backend.
