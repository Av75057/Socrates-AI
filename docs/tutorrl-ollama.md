# TutorRL-7B-think через Ollama

Инструкция для подключения `TutorRL-7B-think` как локальной модели `socrates-tutor-rl` в Socrates-AI.

По состоянию на 22 апреля 2026 года:
- исходная модель доступна на Hugging Face: `eth-nlped/TutorRL-7B-think`
- готовые GGUF-кванты доступны на Hugging Face: `mradermacher/TutorRL-7B-think-GGUF`
- для RTX 4060 8 GB практичный стартовый вариант: `Q4_K_M`

## Быстрый путь

1. Убедитесь, что локально установлен и запущен Ollama.
2. Из корня репозитория выполните:

```bash
chmod +x scripts/setup_tutor_rl.sh
./scripts/setup_tutor_rl.sh
```

Скрипт:
- скачает `TutorRL-7B-think.Q4_K_M.gguf`, если файла ещё нет
- создаст Ollama-модель `socrates-tutor-rl`
- выполнит smoke-test через `scripts/test_tutor_rl.py`

## Ручной импорт

1. Скачайте GGUF в локальную папку, например `models/`:

```bash
huggingface-cli download \
  mradermacher/TutorRL-7B-think-GGUF \
  TutorRL-7B-think.Q4_K_M.gguf \
  --local-dir ./models \
  --local-dir-use-symlinks False
```

2. Обновите строку `FROM` в [TutorRL.Modelfile](/home/andrey/ai-agent/TutorRL.Modelfile), если ваш путь отличается.

3. Импортируйте модель в Ollama:

```bash
ollama create socrates-tutor-rl -f ./TutorRL.Modelfile
ollama list
```

4. Проверьте ответ модели:

```bash
OLLAMA_TUTOR_MODEL=socrates-tutor-rl python3 scripts/test_tutor_rl.py
```

Ожидаемое поведение:
- модель задаёт наводящие вопросы
- модель не должна сразу выдавать решение
- `<think>...</think>` блоки не должны попадать в интерфейс Socrates-AI, backend их срезает

## Если GGUF отсутствует

Если готового GGUF по какой-то причине нет, используйте конвертацию из safetensors:

1. Скачайте `eth-nlped/TutorRL-7B-think`.
2. Соберите `llama.cpp` по официальной инструкции.
3. Выполните конвертацию:

```bash
python convert.py TutorRL-7B-think/ \
  --outfile TutorRL-7B-think-Q4_K_M.gguf \
  --outtype q4_K_M
```

После этого обновите `FROM` в `TutorRL.Modelfile` на фактический путь к `.gguf`.

## Интеграция с Socrates-AI

В `backend/.env`:

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:7b-instruct
OLLAMA_TUTOR_MODEL=socrates-tutor-rl
```

Затем:
- откройте `/admin/llm`
- выберите `Ollama`
- в списке моделей выберите `socrates-tutor-rl`

Админка запрашивает список локальных моделей через `GET /api/tags`.

## Производительность

Целевой ориентир из ТЗ: `10-15 tok/s` на RTX 4060 8 GB.

Это зависит от:
- выбранного кванта
- версии Ollama / llama.cpp
- размера `num_ctx`
- параллельной загрузки GPU

Практически:
- `Q4_K_M` обычно лучший старт по балансу скорости и качества
- `Q5_K_M` имеет смысл, если хватает VRAM и нужен чуть более стабильный вывод
