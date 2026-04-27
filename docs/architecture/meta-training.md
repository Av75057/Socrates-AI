# Meta-Training Architecture

Статус: draft для реализации  
Модуль: `meta_training` / "Эпистемологический спарринг"  
Обновлено: 2026-04-27

## 1. Цель

`meta_training` нужен как отдельный режим Socrates-AI, который тренирует не знание фактов, а качество работы со знанием:

- умение задавать вопросы;
- умение вскрывать допущения;
- умение выбирать и менять рамки;
- умение удерживать неопределённость;
- умение честно описывать границы собственного понимания.

Это не вариация обычного сократического тьютора. Это отдельный сценарий с собственной prompt-архитектурой, состоянием сессии, шкалами оценки и UI.

## 2. Архитектурный принцип

Нужно разделять два слоя:

1. `Current MVP`
   Сейчас режим уже протянут в коде через:
   - [backend/app/routes/meta_training.py](/home/andrey/ai-agent/backend/app/routes/meta_training.py)
   - [backend/app/services/meta_training_service.py](/home/andrey/ai-agent/backend/app/services/meta_training_service.py)
   - [frontend/src/components/meta/MetaTrainingPanel.jsx](/home/andrey/ai-agent/frontend/src/components/meta/MetaTrainingPanel.jsx)

2. `Target Architecture`
   Следующий шаг: вынести prompt-логику, API-контракты и phase-specific orchestration в более чистую структуру, чтобы режим можно было развивать без разрастания одного сервиса.

Этот документ описывает именно целевую архитектуру, сохраняя совместимость с уже реализованным MVP.

## 3. Целевая структура файлов

Рекомендуемая структура backend:

```text
backend/app/
  prompts/
    meta_training/
      base.md
      orientation.md
      framing.md
      sparring.md
      reflection.md
      few_shots.md
  schemas/
    meta_training.py
  services/
    meta_training_service.py
    meta_training_prompt_builder.py
    meta_training_evaluator.py
    meta_training_question_classifier.py
    model_router.py
    llm_service.py  # target façade over ModelRouter for meta-training
  api/v1/
    meta_training.py
```

Примечание по текущему репозиторию:

- каталог `backend/app/prompts/meta_training/` уже есть;
- Pydantic DTO сейчас лежат в [backend/app/dto/meta_training.py](/home/andrey/ai-agent/backend/app/dto/meta_training.py);
- runtime state и orchestration сейчас сосредоточены в [backend/app/services/meta_training_service.py](/home/andrey/ai-agent/backend/app/services/meta_training_service.py);
- structured JSON parsing уже вынесен в [backend/app/services/model_router.py](/home/andrey/ai-agent/backend/app/services/model_router.py);
- evaluator и classifier уже отделены в [backend/app/services/meta_training_evaluator.py](/home/andrey/ai-agent/backend/app/services/meta_training_evaluator.py) и [backend/app/services/meta_training_question_classifier.py](/home/andrey/ai-agent/backend/app/services/meta_training_question_classifier.py).

Это уже лучше, чем исходный MVP. Следующий шаг не "изобрести LLM слой с нуля", а аккуратно оформить поверх текущего `ModelRouter` целевую `LLMService`-façade и вынести Redis-history в явный helper.

## 4. System Prompt Preset

## 4.1. Базовая идентичность

Базовый системный промпт `meta_training` должен собираться динамически, но начинаться с общей identity-части:

```text
Ты — Socrates-AI, но не в режиме тьютора, а в режиме Тренера Эпистемологической Зрелости. Твоя цель — не передать знания, а развить у ученика способность мыслить в условиях неизвестности. Ты действуешь строго по принципам: правила работы со знанием важнее самого знания. Ты — тренер по "серфингу смыслов".

Категорически запрещено:
- ДАВАТЬ ГОТОВЫЕ ОТВЕТЫ.
- ОЦЕНИВАТЬ ФАКТОЛОГИЧЕСКУЮ ПРАВИЛЬНОСТЬ.
- ЗАВЕРШАТЬ ДИСКУССИЮ ИТОГОМ в стиле "правильное понимание таково".

Твои инструменты:
- ВОПРОСЫ, которые вскрывают допущения.
- ПРЕДЛОЖЕНИЕ РАМОК.
- МЕНЮ ИСТОЧНИКОВ.
- ОДОБРЕНИЕ хорошего вопроса.
```

## 4.2. Фазовые добавки к промпту

Перед каждым LLM-вызовом к base prompt добавляется phase-block.

### Phase 1: Orientation

```text
Сейчас Фаза 1: Ориентация.
Ученик видит провокационный тезис. Твоя задача — не объяснять его, а помочь ученику сформулировать как можно больше ВОПРОСОВ к нему.
- Если вопрос слишком общий, помоги его уточнить.
- Предложи классификацию: фактологический, концептуальный, провокационный, мета-вопрос.
- Если ученик не знает, что спросить, подскажи через скрытое допущение.
```

### Phase 2: Framing

```text
Сейчас Фаза 2: Поиск рамок.
Ученик пытается понять, через какую оптику смотреть на проблему.
- Не давай определений. Только МЕНЮ ПОДХОДОВ.
- Предлагай 2-4 рамки.
- После выбора требуй явного обоснования.
- После выбора рамки спрашивай про "вопрос первого шага" внутри неё.
```

### Phase 3: Sparring

```text
Сейчас Фаза 3: Сократический спарринг.
Ты принимаешь на себя роль Защитника Тезиса.
- Отвечай по существу.
- Аргументация должна быть связной и правдоподобной, но не без изъянов.
- Если ученик ударил по слабому месту, признай пробел явно.
- Если ученик слишком быстро согласился, подтолкни к возражению.
```

### Phase 4: Reflection

```text
Сейчас Фаза 4: Рефлексия.
Попроси ученика сформулировать собственное понимание тезиса.
Нужно, чтобы он явно указал:
- в чем уверен;
- в чем не уверен;
- где видит границы своего незнания.
```

## 4.3. Few-shot

Для стабилизации стиля стоит подключить отдельный `few_shots.md` с короткими эталонными диалогами.

Минимум нужен one-shot для `sparring`, например:

```text
User: Ты утверждаешь, что наблюдатель неизбежно влияет на реальность. Но что значит "влияет"? Это физическое воздействие прибора или самим фактом получения информации?
Socrates-AI: В копенгагенской интерпретации имеется в виду второе: акт измерения коллапсирует волновую функцию. Прибор тут ни при чем.
User: Но разве коллапс волновой функции — это не просто математический трюк, а не физический процесс?
Socrates-AI: Ты указал на реальную уязвимость. Моя позиция держится на трактовке коллапса как физического процесса, а это спорное допущение.
```

## 5. Prompt Builder

Нужен отдельный `meta_training_prompt_builder.py`, который собирает prompt из четырех частей:

1. Base identity.
2. Phase-specific block.
3. Session context.
4. Few-shot examples только там, где они реально нужны.

### Session context

В prompt должен подмешиваться контекст сессии:

```text
Тезис: {thesis}
Текущая фаза: {phase}
Выбранная рамка: {chosen_frame or "не выбрана"}
Последние вопросы ученика:
{last_questions}
Последние переключения рамок:
{frame_history}
```

Важно: в prompt нужно передавать не всю историю подряд, а структурированный срез, иначе модель быстро начнет размывать дисциплину режима.

## 5.1. LLM Gateway: Current vs Target

В текущем коде роль LLM gateway уже выполняет [backend/app/services/model_router.py](/home/andrey/ai-agent/backend/app/services/model_router.py). Он:

- выбирает модель и провайдера;
- вызывает OpenRouter или другой OpenAI-compatible endpoint;
- умеет обычный text output;
- умеет structured JSON через `call_model_json(...)`;
- централизованно парсит JSON через `parse_json_object(...)`.

Для `meta_training` это правильная база. Поэтому отдельный `LLMService` не должен дублировать сетевой транспорт. Его задача уже уже:

- собрать сообщения для конкретного сценария;
- выбрать режим вызова: `text` или `json`;
- подмешать context window и few-shot assets;
- скрыть phase-specific prompt engineering от `MetaTrainingService`.

Целевая зависимость должна выглядеть так:

```text
MetaTrainingService
  -> MetaTrainingPromptBuilder
  -> LLMService
       -> ModelRouter
```

Где:

- `ModelRouter` отвечает за transport, provider selection, fallback и JSON extraction;
- `LLMService` отвечает за orchestration уровня сценария;
- `MetaTrainingPromptBuilder` отвечает за текст prompt assets и session context;
- classifier и evaluator используют тот же `LLMService` или напрямую `ModelRouter`, но через одинаковый structured-output contract.

## 5.2. Target LLMService API

Целевой `LLMService` для `meta_training` можно держать очень тонким:

```python
class LLMService:
    def __init__(self, router: ModelRouter, prompt_builder: MetaTrainingPromptBuilder) -> None:
        self.router = router
        self.prompt_builder = prompt_builder

    async def chat_for_session(
        self,
        state: MetaTrainingSessionState,
        user_message: str,
        *,
        temperature: float = 0.4,
        max_tokens: int = 320,
    ) -> str:
        ...

    async def classify_question(
        self,
        thesis: str,
        question: str,
    ) -> dict[str, str | None]:
        ...

    async def evaluate_session(
        self,
        state: MetaTrainingSessionState,
    ) -> dict[str, object]:
        ...

    async def generate_thesis(
        self,
        preferred_topic: str | None = None,
    ) -> str:
        ...
```

Принципиально важно:

- `LLMService` не должен сам парсить JSON руками;
- все structured ответы должны идти через `ModelRouter.call_model_json(...)`;
- phase prompts не должны жить внутри него строковыми литералами;
- few-shot тексты должны приходить из prompt assets, а не быть зашиты в код.

## 5.3. Text Calls vs Structured Calls

Для `meta_training` реально нужны два разных режима вызова.

`Text call`:

- обычный ответ тренера в фазах `orientation`, `exploration`, `sparring`, `reflection`;
- возвращает только текст;
- использует `router.call_model(...)`.

`Structured call`:

- классификация вопроса;
- финальная оценка Wisdom Points;
- в будущем детекция frame shift и mind-map relation labels;
- использует только `router.call_model_json(...)`.

Это уже частично реализовано:

- [backend/app/services/meta_training_question_classifier.py](/home/andrey/ai-agent/backend/app/services/meta_training_question_classifier.py)
- [backend/app/services/meta_training_evaluator.py](/home/andrey/ai-agent/backend/app/services/meta_training_evaluator.py)

То есть документируемый target не абстрактный: он уже начал оформляться в коде.

## 5.4. Redis History Manager

Для `meta_training` стоит ввести отдельный helper поверх Redis, даже если пока transcript живет прямо в session state.

Причина простая: у сессии есть две разные потребности:

- `authoritative session state` для API и UI;
- `compact LLM context window` для prompt assembly.

Целевой helper:

```python
class HistoryManager:
    @staticmethod
    async def add_message(session_id: str, role: str, content: str) -> None:
        ...

    @staticmethod
    async def get_history(session_id: str, limit: int = 20) -> list[dict[str, str]]:
        ...

    @staticmethod
    async def clear_history(session_id: str) -> None:
        ...
```

Рекомендуемый Redis layout:

- `socrates:meta-training:{session_id}`: полный session state;
- `socrates:meta-training:{session_id}:history`: sorted set или list для последних turn-ов;
- `socrates:meta-training:{session_id}:events`: опционально для mind-map и analytics.

Почему это лучше, чем хранить только `transcript` в одном JSON:

- можно ограничивать LLM context без перепаковки всего state;
- проще собирать evaluator context отдельно от UI payload;
- легче масштабировать streaming, analytics и event sourcing.

Важно: `HistoryManager` не должен становиться вторым источником истины о фазе, score и frame history. Источник истины для session orchestration остается `MetaTrainingSessionState`.

## 5.5. Question Classification Contract

Классификация для фазы 1 должна быть дешевой, стабильной и объяснимой.

Целевой structured-output contract:

```json
{
  "question_type": "conceptual",
  "assumption_hint": "Вопрос предполагает, что у термина уже есть единое значение."
}
```

Желаемая стратегия:

1. дешевые heuristics как baseline;
2. короткий LLM JSON call как override;
3. fallback к heuristic result при любой ошибке парсинга или provider failure.

Именно так текущая реализация уже устроена в [backend/app/services/meta_training_question_classifier.py](/home/andrey/ai-agent/backend/app/services/meta_training_question_classifier.py).

Отдельное требование к prompt engineering:

- classifier не должен писать объяснительный текст;
- classifier не должен использовать длинный chain-of-thought;
- classifier должен возвращать один из строго разрешённых enum values: `factual`, `conceptual`, `provocative`, `meta`.

## 5.6. Final Evaluation Contract

Финальная LLM-оценка не должна заменять session-time scoring, а должна корректировать его. Это отдельный assessor call, а не продолжение диалога тем же "голосом".

Целевой JSON:

```json
{
  "inquisitiveness": 0,
  "frame_agility": 0,
  "uncertainty_tolerance": 0,
  "assumption_detection": 0,
  "meta_reflection": 0,
  "comment": "2-4 предложения",
  "confidence": 0.0,
  "flags": ["short_dialog"]
}
```

Где:

- `comment` это короткий развёрнутый комментарий к оценке;
- `confidence` это уверенность асессора в диапазоне `0.0..1.0`;
- `flags` это список risk markers, например `short_dialog`, `low_engagement`, `high_performance`, `possible_gaming`.

Рекомендуемый pipeline:

1. во время сессии копятся heuristic scores;
2. в `end()` evaluator делает отдельный structured LLM pass по полной истории;
3. LLM оценивает только реплики ученика, а реплики assistant использует как контекст;
4. итог по каждой шкале берется как нормализация поверх baseline;
5. confidence и flags сохраняются вместе с результатом;
6. уже после этого считается reward и обновляется профиль ученика.

Текущий код следует почти этому же направлению:

- [backend/app/services/meta_training_service.py](/home/andrey/ai-agent/backend/app/services/meta_training_service.py)
- [backend/app/services/meta_training_evaluator.py](/home/andrey/ai-agent/backend/app/services/meta_training_evaluator.py)

Но текущая реализация пока проще целевого состояния:

- evaluator возвращает `scores + summary`;
- `confidence` и `flags` ещё не добавлены в контракт;
- prompt уже строгий, но ещё не содержит явной рубрики по диапазонам `0-2`, `3-5`, `6-8`, `9-10`.

## 5.7. Few-Shot Asset Strategy

Few-shot примеры для `meta_training` не стоит размазывать по коду.

Правильная организация:

- `base.md`: identity и hard rules режима;
- `orientation.md`, `framing.md`, `sparring.md`, `reflection.md`: phase prompts;
- `few_shots.md`: короткие эталонные куски диалога;
- `question_classifier.md`: structured classifier prompt;
- `evaluator.md`: structured evaluator prompt.

Правило подключения:

- `few_shots.md` не нужно добавлять всегда;
- для `sparring` few-shot особенно полезен;
- для classifier и evaluator few-shot обычно не нужен, там важнее короткий schema-first prompt.

Это уже соответствует текущей структуре каталога [backend/app/prompts/meta_training](/home/andrey/ai-agent/backend/app/prompts/meta_training).

## 6. API Contract

Целевой API:

```text
POST /api/v1/meta-training/start
POST /api/v1/meta-training/message
GET  /api/v1/meta-training/status/{session_id}
POST /api/v1/meta-training/end
```

Примечание:

- path-based endpoint уже реализован: `GET /api/v1/meta-training/status/{session_id}`;
- query-style `status?session_id=...` оставлен только как backward-compatible alias.

## 6.1. Pydantic Models

Целевая схема:

```python
from pydantic import BaseModel
from typing import Optional
from enum import Enum
import datetime

class MetaPhase(str, Enum):
    ORIENTATION = "orientation"
    FRAMING = "framing"
    SPARRING = "sparring"
    REFLECTION = "reflection"

class QuestionType(str, Enum):
    FACTUAL = "factual"
    CONCEPTUAL = "conceptual"
    PROVOCATIVE = "provocative"
    META = "meta"

class MetaSessionStartRequest(BaseModel):
    topic_provided_by_user: Optional[str] = None

class MetaMessageRequest(BaseModel):
    session_id: str
    message: str

class MetaSessionState(BaseModel):
    session_id: str
    current_phase: MetaPhase
    phase_start_time: datetime.datetime
    thesis: str
    chosen_frame: Optional[str] = None
    questions_asked: int = 0
    wisdom_points: Optional[dict] = None

class MetaMessageResponse(BaseModel):
    ai_message: str
    session_state: MetaSessionState
    detected_question_type: Optional[QuestionType] = None
```

Примечание по расхождению с MVP:

- в текущем коде состояние богаче и включает transcript, frame history, raw scores, reward info;
- для public API это допустимо, но наружный контракт лучше стабилизировать и не светить лишнюю внутреннюю механику без необходимости.

## 7. Session State

State хранится в Redis.

Минимальный состав:

```json
{
  "session_id": "meta_...",
  "current_phase": "orientation",
  "phase_start_time": "2026-04-27T12:00:00Z",
  "thesis": "Энтропия — это мера нашего незнания...",
  "chosen_frame": null,
  "questions": [],
  "frames": [],
  "messages": [],
  "scores": {
    "inquisitiveness": 0,
    "frame_agility": 0,
    "uncertainty_tolerance": 0,
    "assumption_detection": 0,
    "meta_reflection": 0
  }
}
```

Отдельно нужно хранить:

- `phase_started_at`;
- `time_remaining_seconds`;
- `role_label`;
- `reward_applied`;
- `awarded_wisdom_points`.

## 8. Backend Flow

## 8.1. Start

`POST /start`:

1. Получить тему от пользователя или сгенерировать тезис.
2. Создать `session_id`.
3. Инициализировать state в фазе `orientation`.
4. Сохранить state в Redis.
5. Вернуть thesis и стартовую реплику AI.

### Генерация тезиса

Если пользователь тему не дал, LLM получает простой task prompt:

```text
Сгенерируй один провокационный тезис для эпистемологической тренировки.
Требования:
- тема должна быть не банальной;
- тезис должен быть спорным, но обсуждаемым;
- тезис должен провоцировать вопросы, а не фактологический ответ;
- ответ — одна фраза, без пояснений.
```

На MVP допустим и curated тезис-library без LLM.

## 8.2. Message

`POST /message`:

1. Прочитать state из Redis.
2. Проверить фазовый timeout.
3. При необходимости продвинуть фазу.
4. В фазе `orientation` классифицировать вопрос.
5. В фазе `framing` детектировать выбор рамки.
6. Собрать системный prompt.
7. Отправить запрос в LLM.
8. Сохранить user/assistant turns.
9. Вернуть AI reply и обновленное состояние.

## 8.3. End

`POST /end`:

1. Принять финальную рефлексию.
2. Запустить evaluation.
3. Начислить Wisdom Points.
4. Сохранить session result в БД.
5. Вернуть финальный radar payload.

## 9. Classification

Фазе 1 нужен быстрый question classifier.

Подход:

1. Сначала cheap heuristics.
2. Если эвристики неуверенны, короткий structured LLM call.

Примеры heuristics:

- `что значит`, `в каком смысле` -> `conceptual`
- `почему`, `зачем`, `что если` -> `provocative`
- `как мы узнаем`, `по каким критериям`, `что считать знанием` -> `meta`
- всё остальное по умолчанию -> `factual`

Нужен structured result:

```json
{
  "question_type": "conceptual",
  "assumption_hint": "Вопрос предполагает, что у термина уже есть единое значение."
}
```

## 10. Frame Detection

Фаза 2 требует explicit frame capture.

Нужно распознавать:

- явный выбор: "беру рамку теории информации";
- неявный выбор: "давай смотреть на это как на проблему языка";
- кнопочный выбор с фронта: `switch_frame(frame_name)`.

Минимальный backend output:

```json
{
  "chosen_frame": "теория информации",
  "reason": "мне легче думать через неопределенность, чем через физические процессы"
}
```

## 11. Evaluation and Wisdom Points

Оценка должна быть не по "правильности", а по процессу.

Шкалы:

- `inquisitiveness`
- `frame_agility`
- `uncertainty_tolerance`
- `assumption_detection`
- `meta_reflection`

Каждая шкала: `0..10`.

## 11.1. MVP Scoring

На MVP можно использовать hybrid scoring:

- heuristic increments during session;
- final LLM pass корректирует и нормализует оценки.

Принципиально важно: итоговую оценку делает не тот же ответный prompt, который вёл тренировку, а отдельный LLM-assessor. Это снижает self-bias и удерживает границу между "тренером" и "методологом".

## 11.2. Final Evaluation Prompt

Нужен отдельный evaluator prompt. Его задача не "понять, прав ли ученик", а строго оценить качество мышления по пяти шкалам.

```text
Ты — Эксперт по оценке мета-компетенций (эпистемологической зрелости). Твоя задача — проанализировать диалог ученика с ИИ-тренером и выставить баллы по пяти шкалам.

Шкалы:
- inquisitiveness: задает ли он разнообразные и осмысленные вопросы;
- frame_agility: умеет ли осознанно менять перспективу;
- uncertainty_tolerance: выдерживает ли незнание без поспешной догмы;
- assumption_detection: вскрывает ли скрытые предпосылки;
- meta_reflection: честно ли описывает границы понимания.

Рубрика:
- 0-2: минимальное проявление навыка;
- 3-5: навык проявлен слабо или эпизодически;
- 6-8: устойчивое качественное проявление;
- 9-10: редкий, почти образцовый уровень.

Верни JSON:
{
  "inquisitiveness": 0..10,
  "frame_agility": 0..10,
  "uncertainty_tolerance": 0..10,
  "assumption_detection": 0..10,
  "meta_reflection": 0..10,
  "comment": "краткий развернутый комментарий",
  "confidence": 0.0..1.0,
  "flags": ["short_dialog", "low_engagement"]
}
```

Ключевые требования к prompt:

- оцениваются только реплики `user`;
- реплики `assistant` это контекст, а не объект оценки;
- если у ученика меньше 4 содержательных реплик, нужно снижать `confidence` и выставлять `short_dialog`;
- `10` по любой шкале это исключительный, а не обычный результат;
- никаких объяснений вне JSON.

Рекомендуемое местоположение prompt asset:

- [backend/app/prompts/meta_training/evaluator.md](/home/andrey/ai-agent/backend/app/prompts/meta_training/evaluator.md)

Текущий prompt уже существует, но его стоит усилить именно до этой схемы.

## 11.3. Evaluation Input Context

В assessor call должны входить:

- тезис;
- выбранная рамка или последняя активная рамка;
- полная история сессии или компактный, но полный по смыслу transcript;
- фазовая разметка сообщений;
- итоговая рефлексия и выбранный уровень уверенности, если пользователь их задал.

Рекомендуемый формат контекста:

```text
Тезис: {thesis}
Выбранная рамка: {frame or "не выбрана"}
Итоговая рефлексия: {reflection_summary or "нет"}
Уровень уверенности ученика: {confidence_label or "не указан"}

Диалог:
user (orientation): ...
assistant (orientation): ...
user (sparring): ...
assistant (sparring): ...
```

Для evaluator важнее целостность хода мысли, чем буквальная полнота всех реплик. Если используется усечённый transcript, он должен сохранять:

- первый импульс вопросов;
- момент выбора рамки;
- наиболее содержательный кусок sparring;
- финальную рефлексию.

## 11.4. Post-Processing and Wisdom Payload

После structured-output вызова raw assessment нужно приводить к стабильному внутреннему payload.

Целевой runtime payload:

```json
{
  "scales": {
    "inquisitiveness": 7,
    "frame_agility": 5,
    "uncertainty_tolerance": 6,
    "assumption_detection": 7,
    "meta_reflection": 4
  },
  "total": 29,
  "comment": "Ученик хорошо атакует допущения, но рефлексия пока короче и слабее остальной сессии.",
  "confidence": 0.82,
  "flags": ["short_reflection"]
}
```

Порядок постобработки:

1. распарсить JSON через `ModelRouter.call_model_json(...)`;
2. привести все шкалы к `int` и зажать в диапазон `0..10`;
3. вычислить `total`;
4. нормализовать `confidence` к диапазону `0.0..1.0`;
5. очистить `flags` до известного allowlist;
6. объединить LLM-оценку с heuristic baseline.

Рекомендуемая стратегия объединения на MVP:

- использовать session-time heuristics как baseline;
- использовать assessor как corrective pass;
- на первом этапе допустима схема `max(heuristic, evaluated)` по каждой шкале, если цель не занижать сильные реальные проявления;
- на следующем этапе лучше перейти к более строгой blend-логике с учетом `confidence` и `flags`.

## 11.5. Reward Formula

Базовый reward можно оставить простым:

```text
wisdom_reward = max(15, total_score * 3)
```

Но reward должен зависеть не только от `total`, а со временем и от `confidence`.

Пример target-логики:

- если есть `short_dialog`, reward начисляется, но помечается как low-confidence;
- если `confidence < 0.55`, результат участвует в истории, но слабее влияет на профиль;
- если есть `possible_gaming`, reward начисляется, но с флагом для Educator Dashboard.

Где:

- `total_score = sum(five_scales)`;
- максимум: `50`;
- максимум награды: `150`.

Это уже реализовано в MVP в упрощённом виде и может остаться baseline.

## 11.6. Profile Aggregation

Цель профиля не "лидерборд", а история развития мета-компетенций.

Для каждой шкалы в профиле полезно хранить:

- `sum`;
- `count`;
- `last_value`;
- `trend`;
- `last_confidence`;
- `flags` последних сессий.

Концептуальная схема:

```python
meta_skills[scale] = {
    "sum": 0,
    "count": 0,
    "last_value": 0,
    "last_confidence": 0.0,
    "trend": "stable"
}
```

Правила обновления:

1. `sum += value`
2. `count += 1`
3. `trend = up/down/stable` по сравнению с `last_value`
4. `last_confidence = session.confidence`
5. low-confidence sessions не игнорируются, но должны быть визуально помечены

Итоговый `meta_index` можно считать как среднее по средним пяти шкал, но в UI важно показывать не только индекс, а форму профиля и динамику.

## 11.7. Edge Cases and Anti-Gaming

Нужно сразу зафиксировать защиту от очевидных искажений:

1. `short_dialog`
   Если диалог слишком короткий, результат сохраняется, но confidence занижается и в dashboard он маркируется отдельно.

2. `low_engagement`
   Если ученик почти не включился, ассессор не должен натягивать высокие оценки за одну удачную реплику.

3. `possible_gaming`
   Если паттерн реплик выглядит как шаблонное воспроизведение "идеальных фраз", это не повод автоматически обнулять результат, но это повод поднять флаг.

4. assessor uncertainty
   Даже хороший evaluator может ошибаться. Поэтому manual override со стороны педагога должен быть допустимым уровнем системы, а не аварийным костылём.

5. rubric drift
   Когда появятся размеченные эталонные диалоги, evaluator prompt и scoring rules нужно будет валидировать на согласованность с экспертной разметкой.

## 12. Persistence

Нужно сохранять итоги сессии в БД, чтобы:

- строить историю мета-тренировок;
- показывать динамику по шкалам;
- отдавать данные в Educator Dashboard;
- подбирать следующие темы.

Текущая таблица:

- [backend/app/db/models.py](/home/andrey/ai-agent/backend/app/db/models.py:418)
- миграция [backend/alembic/versions/20260427_0012_meta_training_sessions.py](/home/andrey/ai-agent/backend/alembic/versions/20260427_0012_meta_training_sessions.py)

Минимальные поля:

- `user_id`
- `session_key`
- `thesis`
- `topic_slug`
- `scores`
- `questions`
- `frames`
- `transcript`
- `reflection_summary`
- `confidence_label`
- `awarded_wisdom_points`
- `started_at`
- `ended_at`

## 13. Frontend Contract

Фронту от backend нужны не только сообщения, но и отдельный session payload:

```json
{
  "session_id": "meta_...",
  "phase": "sparring",
  "role_label": "Защитник тезиса",
  "thesis": "В квантовой механике наблюдатель влияет на реальность...",
  "time_remaining_seconds": 421,
  "questions": [...],
  "frames": [...],
  "scores": {
    "inquisitiveness": 6,
    "frame_agility": 4,
    "uncertainty_tolerance": 5,
    "assumption_detection": 3,
    "meta_reflection": 0,
    "total": 18
  }
}
```

Это уже близко к текущему MVP API.

## 14. Mind-Map Contract

Следующий этап, не MVP.

Frontend должен получать graph-friendly nodes:

```json
{
  "nodes": [
    {"id": "q1", "type": "question", "label": "..."},
    {"id": "q2", "type": "question", "label": "..."},
    {"id": "a1", "type": "counterargument", "label": "..."}
  ],
  "edges": [
    {"from": "q1", "to": "q2", "relation": "clarifies"},
    {"from": "q2", "to": "a1", "relation": "challenges"}
  ]
}
```

Сейчас этого контракта нет, и это осознанно вынесено за рамки MVP.

## 15. Open Questions

Ниже вопросы, которые ещё не закрыты архитектурно:

1. Оформляем ли мы отдельный `LLMService`-façade поверх `ModelRouter`, или оставляем classifier/evaluator/service напрямую зависимыми от `ModelRouter`?
2. Хотим ли мы phase transition только по кнопке/таймеру, или вводим quality-based auto-advance?
3. Нужно ли делать отдельный `meta_training` conversation type в общей истории пользователя?
4. Храним ли compact history в отдельном Redis key-space уже сейчас, или откладываем до streaming/mind-map этапа?
5. Как именно взвешивать low-confidence sessions при расчёте профиля?
6. Как именно отображать сравнительную динамику нескольких meta-сессий в educator dashboard?

## 16. Recommended Next Steps

Если двигаться инженерно правильно, следующий порядок такой:

1. Вынести Redis transcript access в отдельный `HistoryManager`, не ломая текущий `MetaTrainingSessionState`.
2. Решить, нужен ли отдельный `LLMService`-façade для сценарной orchestration поверх `ModelRouter`.
3. Перенести phase-1 coaching hints в backend recommendation layer, чтобы логика была общей для web/mobile.
4. После этого подключать mind-map и dashboard analytics.

## 17. Decision

Сразу `git push` делать рано.

Сначала стоит добить два подпункта, которые дадут наибольший архитектурный эффект:

1. `LLMService / HistoryManager`
   Prompt builder уже есть, а вот orchestration-слой над `ModelRouter` и отдельный history helper ещё не оформлены.

2. `Wisdom Points evaluator`
   Базовая версия уже есть, но её ещё можно усиливать richer context и более строгим scoring prompt.

Если выбирать один следующий рабочий шаг, то правильнее брать `HistoryManager` и compact context policy. Это даст реальный выигрыш и для prompt discipline, и для будущего mind-map слоя.
