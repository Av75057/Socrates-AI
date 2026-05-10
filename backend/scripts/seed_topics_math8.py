from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.models import Topic, User
from app.db.session import SessionLocal
from app.services.learning_service import normalize_learning_objectives


@dataclass(frozen=True)
class TopicSeed:
    title: str
    description: str
    initial_prompt: str
    difficulty: int
    tags: list[str]
    learning_objectives: list[dict[str, object]]


TOPICS: list[TopicSeed] = [
    TopicSeed(
        title="Рациональные дроби: как увидеть общий множитель?",
        description="Учимся замечать структуру выражения и сокращать рациональные дроби осмысленно, а не по шаблону.",
        initial_prompt="Если в числителе и знаменателе есть похожие части, как понять, что именно можно вынести за скобки?",
        difficulty=2,
        tags=["математика", "8класс", "алгебра", "рациональныедроби"],
        learning_objectives=[
            {"title": "Строит связное объяснение сокращения дроби", "skill_id": "structure_argument", "target_level": 55},
            {"title": "Проверяет идею на контрпримере", "skill_id": "use_counterexample", "target_level": 45},
        ],
    ),
    TopicSeed(
        title="Допустимые значения переменной в дробном выражении",
        description="Разбираем, почему нельзя подставлять любые числа и как находить ограничения до преобразований.",
        initial_prompt="Почему в дробном выражении важно сначала подумать, при каких значениях знаменатель обращается в ноль?",
        difficulty=2,
        tags=["математика", "8класс", "алгебра", "одз"],
        learning_objectives=[
            {"title": "Задаёт уточняющие вопросы про ограничения", "skill_id": "ask_clarifying", "target_level": 50},
            {"title": "Соблюдает логическую последовательность рассуждения", "skill_id": "logical_consistency", "target_level": 55},
        ],
    ),
    TopicSeed(
        title="Сложение и вычитание алгебраических дробей",
        description="Переходим от механики к пониманию: когда нужен общий знаменатель и как его выбирать.",
        initial_prompt="Если знаменатели разные, как ты бы объяснил необходимость общего знаменателя человеку, который видит тему впервые?",
        difficulty=3,
        tags=["математика", "8класс", "алгебра", "дроби"],
        learning_objectives=[
            {"title": "Строит аргумент шаг за шагом", "skill_id": "structure_argument", "target_level": 60},
            {"title": "Соблюдает логику при преобразованиях", "skill_id": "logical_consistency", "target_level": 60},
        ],
    ),
    TopicSeed(
        title="Умножение и деление алгебраических дробей",
        description="Тренируем понимание структуры выражения и проверку, где сокращение допустимо, а где нет.",
        initial_prompt="Чем сокращение множителей отличается от сокращения слагаемых, и как это проверить на примере?",
        difficulty=3,
        tags=["математика", "8класс", "алгебра", "дроби"],
        learning_objectives=[
            {"title": "Использует контрпример против ошибочного сокращения", "skill_id": "use_counterexample", "target_level": 60},
            {"title": "Сохраняет логическую строгость преобразований", "skill_id": "logical_consistency", "target_level": 55},
        ],
    ),
    TopicSeed(
        title="Степень с целым показателем: смысл и примеры",
        description="Разбираем, что на самом деле означает отрицательная и нулевая степень, и почему правила работают.",
        initial_prompt="Как бы ты объяснил, почему число в нулевой степени равно единице, не ссылаясь только на правило из учебника?",
        difficulty=3,
        tags=["математика", "8класс", "алгебра", "степени"],
        learning_objectives=[
            {"title": "Приводит осмысленный контрпример или проверку", "skill_id": "use_counterexample", "target_level": 50},
            {"title": "Строит связное объяснение математического правила", "skill_id": "structure_argument", "target_level": 60},
        ],
    ),
    TopicSeed(
        title="Свойства степеней без заучивания",
        description="Не зубрим формулы, а выводим их на простых примерах и замечаем, где они перестают работать.",
        initial_prompt="Как можно самому вывести правило a^m · a^n = a^(m+n), если взять конкретные небольшие степени?",
        difficulty=3,
        tags=["математика", "8класс", "алгебра", "степени"],
        learning_objectives=[
            {"title": "Выводит правило через примеры", "skill_id": "structure_argument", "target_level": 65},
            {"title": "Проверяет правило на частных случаях", "skill_id": "use_counterexample", "target_level": 50},
        ],
    ),
    TopicSeed(
        title="Стандартный вид числа и порядок величин",
        description="Понимаем, зачем стандартный вид нужен в науке, и учимся интерпретировать очень большие и очень малые числа.",
        initial_prompt="Почему запись 3,2·10^5 иногда удобнее обычной, и что она помогает увидеть сразу?",
        difficulty=2,
        tags=["математика", "8класс", "алгебра", "стандартныйвид"],
        learning_objectives=[
            {"title": "Уточняет смысл математической записи", "skill_id": "ask_clarifying", "target_level": 45},
            {"title": "Строит короткое и точное объяснение", "skill_id": "structure_argument", "target_level": 50},
        ],
    ),
    TopicSeed(
        title="Квадратный корень: что означает знак √",
        description="Осваиваем идею квадратного корня как обратного действия и разбираем, где интуиция подводит.",
        initial_prompt="Если √a — это число, квадрат которого равен a, то как ты бы проверил, что понял это определение правильно?",
        difficulty=2,
        tags=["математика", "8класс", "алгебра", "квадратныйкорень"],
        learning_objectives=[
            {"title": "Проверяет определение на примерах", "skill_id": "use_counterexample", "target_level": 50},
            {"title": "Не допускает логических противоречий в определениях", "skill_id": "logical_consistency", "target_level": 55},
        ],
    ),
    TopicSeed(
        title="Свойства квадратных корней",
        description="Разбираем, когда можно разносить корень по произведению и почему с суммой этот приём не работает.",
        initial_prompt="Почему √(a+b) обычно нельзя заменить на √a + √b, и как это быстро проверить самому?",
        difficulty=3,
        tags=["математика", "8класс", "алгебра", "корни"],
        learning_objectives=[
            {"title": "Использует контрпример против ложного правила", "skill_id": "use_counterexample", "target_level": 65},
            {"title": "Аргументирует без подмены тезиса", "skill_id": "avoid_straw_man", "target_level": 45},
        ],
    ),
    TopicSeed(
        title="Линейная функция y = kx + b",
        description="Понимаем, как коэффициенты влияют на график и что они говорят о поведении функции.",
        initial_prompt="Если изменить только коэффициент k, что именно произойдёт с графиком и почему?",
        difficulty=2,
        tags=["математика", "8класс", "алгебра", "функции"],
        learning_objectives=[
            {"title": "Строит причинно-следственное объяснение", "skill_id": "structure_argument", "target_level": 55},
            {"title": "Задаёт уточняющие вопросы о параметрах", "skill_id": "ask_clarifying", "target_level": 45},
        ],
    ),
    TopicSeed(
        title="Графики линейных функций: как читать пересечения",
        description="Учимся видеть в графике уравнение и понимать, что означает точка пересечения двух прямых.",
        initial_prompt="Если две прямые пересекаются, как можно объяснить смысл координат этой точки без формальных слов?",
        difficulty=3,
        tags=["математика", "8класс", "алгебра", "графики"],
        learning_objectives=[
            {"title": "Связывает график и алгебраическую модель", "skill_id": "structure_argument", "target_level": 60},
            {"title": "Сохраняет логическую точность интерпретации", "skill_id": "logical_consistency", "target_level": 55},
        ],
    ),
    TopicSeed(
        title="Системы линейных уравнений: смысл решения",
        description="Не просто решаем систему, а понимаем, почему решение должно удовлетворять обоим уравнениям одновременно.",
        initial_prompt="Почему недостаточно, чтобы пара чисел подходила только к одному уравнению системы?",
        difficulty=3,
        tags=["математика", "8класс", "алгебра", "системыуравнений"],
        learning_objectives=[
            {"title": "Соблюдает логическую строгость определения решения", "skill_id": "logical_consistency", "target_level": 60},
            {"title": "Строит ясный аргумент про оба уравнения сразу", "skill_id": "structure_argument", "target_level": 60},
        ],
    ),
    TopicSeed(
        title="Метод подстановки в системах уравнений",
        description="Разбираем, когда подстановка удобна и как не потерять смысл преобразований за алгоритмом.",
        initial_prompt="Как понять, какое уравнение удобнее выразить первым, если ты хочешь решить систему подстановкой?",
        difficulty=3,
        tags=["математика", "8класс", "алгебра", "подстановка"],
        learning_objectives=[
            {"title": "Задаёт уточняющие вопросы о выборе шага", "skill_id": "ask_clarifying", "target_level": 50},
            {"title": "Строит последовательное объяснение алгоритма", "skill_id": "structure_argument", "target_level": 60},
        ],
    ),
    TopicSeed(
        title="Квадратные уравнения: когда корней может не быть?",
        description="Вводим квадратные уравнения через смысл графика и анализа выражения, а не только через формулы.",
        initial_prompt="Как ты бы объяснил идею «уравнение может не иметь действительных корней», если смотреть на график?",
        difficulty=4,
        tags=["математика", "8класс", "алгебра", "квадратныеуравнения"],
        learning_objectives=[
            {"title": "Аргументирует через несколько представлений задачи", "skill_id": "structure_argument", "target_level": 65},
            {"title": "Не смешивает разные случаи решения", "skill_id": "logical_consistency", "target_level": 60},
        ],
    ),
    TopicSeed(
        title="Разложение многочлена на множители: зачем это вообще делать?",
        description="Понимаем, как разложение помогает упростить выражение, решить уравнение и увидеть структуру задачи.",
        initial_prompt="Если выражение можно разложить на множители, что это даёт тебе по сравнению с исходной записью?",
        difficulty=3,
        tags=["математика", "8класс", "алгебра", "многочлены"],
        learning_objectives=[
            {"title": "Объясняет смысл преобразования, а не только шаг", "skill_id": "structure_argument", "target_level": 60},
            {"title": "Сохраняет логическую точность при преобразовании", "skill_id": "logical_consistency", "target_level": 55},
        ],
    ),
    TopicSeed(
        title="Формулы сокращённого умножения: как не зубрить, а узнавать",
        description="Учимся видеть шаблоны в выражениях и проверять формулы на простых числах и контрпримерах.",
        initial_prompt="Как самому проверить формулу (a+b)^2, если ты не хочешь просто верить учебнику на слово?",
        difficulty=3,
        tags=["математика", "8класс", "алгебра", "сокращенноеумножение"],
        learning_objectives=[
            {"title": "Проверяет формулу на примере", "skill_id": "use_counterexample", "target_level": 55},
            {"title": "Строит связное объяснение раскрытия скобок", "skill_id": "structure_argument", "target_level": 60},
        ],
    ),
    TopicSeed(
        title="Разность квадратов и её ловушки",
        description="Разбираем, когда формула a^2-b^2 действительно применима и где похожий вид может обмануть.",
        initial_prompt="По каким признакам ты отличишь настоящую разность квадратов от выражения, которое только похоже на неё?",
        difficulty=3,
        tags=["математика", "8класс", "алгебра", "разностьквадратов"],
        learning_objectives=[
            {"title": "Отличает корректный шаблон от ложного", "skill_id": "logical_consistency", "target_level": 60},
            {"title": "Опровергает ошибочную догадку контрпримером", "skill_id": "use_counterexample", "target_level": 55},
        ],
    ),
    TopicSeed(
        title="Системы линейных уравнений: метод сложения",
        description="Смотрим, когда выгодно складывать уравнения и как выбирать коэффициенты осмысленно.",
        initial_prompt="Как понять заранее, что для этой системы метод сложения удобнее подстановки?",
        difficulty=3,
        tags=["математика", "8класс", "алгебра", "методсложения"],
        learning_objectives=[
            {"title": "Задаёт уточняющие вопросы о выборе метода", "skill_id": "ask_clarifying", "target_level": 50},
            {"title": "Объясняет ход решения шаг за шагом", "skill_id": "structure_argument", "target_level": 60},
        ],
    ),
    TopicSeed(
        title="Линейные неравенства: чем они отличаются от уравнений",
        description="Разбираем, почему ответом становится промежуток и что меняется при умножении на отрицательное число.",
        initial_prompt="Почему при умножении неравенства на отрицательное число знак нужно менять, и как это убедительно проверить?",
        difficulty=3,
        tags=["математика", "8класс", "алгебра", "неравенства"],
        learning_objectives=[
            {"title": "Проверяет правило на конкретных числах", "skill_id": "use_counterexample", "target_level": 55},
            {"title": "Сохраняет логическую строгость при переходах", "skill_id": "logical_consistency", "target_level": 60},
        ],
    ),
    TopicSeed(
        title="Задачи на движение через линейные модели",
        description="Переводим текст задачи в таблицу величин и уравнение, не теряя смысл переменных.",
        initial_prompt="Если в задаче есть скорость, время и расстояние, с какой величины ты бы начал построение модели и почему?",
        difficulty=4,
        tags=["математика", "8класс", "алгебра", "текстовыезадачи"],
        learning_objectives=[
            {"title": "Задаёт уточняющие вопросы к условиям задачи", "skill_id": "ask_clarifying", "target_level": 55},
            {"title": "Строит последовательную математическую модель", "skill_id": "structure_argument", "target_level": 65},
        ],
    ),
    TopicSeed(
        title="Задачи на совместную работу и производительность",
        description="Учимся видеть скорость работы как величину и строить модель без механического подбора формулы.",
        initial_prompt="Если два человека делают работу вместе, как описать вклад каждого так, чтобы не запутаться в единицах?",
        difficulty=4,
        tags=["математика", "8класс", "алгебра", "производительность"],
        learning_objectives=[
            {"title": "Уточняет смысл единиц и переменных", "skill_id": "ask_clarifying", "target_level": 55},
            {"title": "Соблюдает логическую непротиворечивость модели", "skill_id": "logical_consistency", "target_level": 60},
        ],
    ),
    TopicSeed(
        title="Теорема Пифагора: от идеи к применению",
        description="Разбираем, что именно связывает теорема Пифагора и почему её нельзя применять к любому треугольнику.",
        initial_prompt="Почему в формулировке теоремы Пифагора так важно условие прямого угла?",
        difficulty=3,
        tags=["математика", "8класс", "геометрия", "пифагор"],
        learning_objectives=[
            {"title": "Проверяет границы применимости теоремы", "skill_id": "use_counterexample", "target_level": 60},
            {"title": "Не искажает условия задачи", "skill_id": "avoid_straw_man", "target_level": 45},
        ],
    ),
    TopicSeed(
        title="Четырёхугольники и их свойства",
        description="Сравниваем признаки и свойства параллелограмма, прямоугольника, ромба и квадрата.",
        initial_prompt="Какие свойства квадрата ты бы назвал «наследованными», а какие требуют отдельного обоснования?",
        difficulty=3,
        tags=["математика", "8класс", "геометрия", "четырехугольники"],
        learning_objectives=[
            {"title": "Сравнивает свойства без подмены понятий", "skill_id": "avoid_straw_man", "target_level": 50},
            {"title": "Строит чёткую классификацию фигур", "skill_id": "structure_argument", "target_level": 60},
        ],
    ),
    TopicSeed(
        title="Площадь треугольника и трапеции: откуда берутся формулы",
        description="Не просто применяем формулы, а выводим их из уже известных площадей и разбиений фигур.",
        initial_prompt="Как можно самому вывести формулу площади трапеции, если ты уже уверен в формуле площади прямоугольника?",
        difficulty=3,
        tags=["математика", "8класс", "геометрия", "площади"],
        learning_objectives=[
            {"title": "Выводит новую формулу из известных", "skill_id": "structure_argument", "target_level": 65},
            {"title": "Сохраняет логическую непротиворечивость вывода", "skill_id": "logical_consistency", "target_level": 55},
        ],
    ),
    TopicSeed(
        title="Средняя линия треугольника: почему она параллельна стороне?",
        description="Не просто запоминаем свойство, а разбираем, откуда оно возникает и как помогает в задачах.",
        initial_prompt="Если соединить середины двух сторон треугольника, почему новая линия вообще должна быть связана с третьей стороной?",
        difficulty=3,
        tags=["математика", "8класс", "геометрия", "средняялиния"],
        learning_objectives=[
            {"title": "Строит доказательное объяснение свойства", "skill_id": "structure_argument", "target_level": 65},
            {"title": "Не перескакивает через логические шаги", "skill_id": "logical_consistency", "target_level": 55},
        ],
    ),
    TopicSeed(
        title="Высота, медиана и биссектриса: как не путать",
        description="Сравниваем три важных отрезка в треугольнике и разбираем их роли на чертеже и в рассуждении.",
        initial_prompt="По каким признакам на рисунке ты отличишь медиану от биссектрисы, если подписи стёрты?",
        difficulty=2,
        tags=["математика", "8класс", "геометрия", "треугольник"],
        learning_objectives=[
            {"title": "Уточняет определения геометрических объектов", "skill_id": "ask_clarifying", "target_level": 50},
            {"title": "Не подменяет одно свойство другим", "skill_id": "avoid_straw_man", "target_level": 45},
        ],
    ),
    TopicSeed(
        title="Окружность и касательная: что значит «касается в одной точке»",
        description="Разбираем смысл касательной и радиуса к точке касания, чтобы не сводить тему к одному правилу.",
        initial_prompt="Почему радиус, проведённый в точку касания, должен быть перпендикулярен касательной?",
        difficulty=3,
        tags=["математика", "8класс", "геометрия", "окружность"],
        learning_objectives=[
            {"title": "Строит связное геометрическое объяснение", "skill_id": "structure_argument", "target_level": 60},
            {"title": "Сохраняет точность условий и выводов", "skill_id": "logical_consistency", "target_level": 55},
        ],
    ),
    TopicSeed(
        title="Центральный и вписанный углы",
        description="Учимся видеть, как один и тот же дуговой фрагмент связан с разными типами углов.",
        initial_prompt="Если два угла опираются на одну и ту же дугу, почему их величины связаны, но не одинаковы?",
        difficulty=4,
        tags=["математика", "8класс", "геометрия", "углы"],
        learning_objectives=[
            {"title": "Сравнивает связанные геометрические объекты без подмены", "skill_id": "avoid_straw_man", "target_level": 50},
            {"title": "Выстраивает причинно-следственное объяснение связи углов", "skill_id": "structure_argument", "target_level": 65},
        ],
    ),
    TopicSeed(
        title="Площади подобных фигур: как работает масштаб",
        description="Связываем подобие с площадью и разбираем, почему линейный коэффициент нельзя переносить на площадь без изменения.",
        initial_prompt="Если стороны фигуры увеличили в 2 раза, почему площадь не увеличивается просто в 2 раза?",
        difficulty=4,
        tags=["математика", "8класс", "геометрия", "подобие", "площади"],
        learning_objectives=[
            {"title": "Опровергает интуитивную ошибку числовым примером", "skill_id": "use_counterexample", "target_level": 60},
            {"title": "Соблюдает логическую точность при работе с масштабом", "skill_id": "logical_consistency", "target_level": 60},
        ],
    ),
    TopicSeed(
        title="Теорема Пифагора в обратную сторону",
        description="Разбираем, как по длинам сторон понять, прямоугольный ли треугольник, и почему это не та же самая задача.",
        initial_prompt="Чем проверка a²+b²=c² отличается по смыслу от обычного применения теоремы Пифагора?",
        difficulty=3,
        tags=["математика", "8класс", "геометрия", "обратнаятеорема"],
        learning_objectives=[
            {"title": "Различает прямую и обратную теорему", "skill_id": "logical_consistency", "target_level": 60},
            {"title": "Проверяет условие на конкретном примере", "skill_id": "use_counterexample", "target_level": 50},
        ],
    ),
    TopicSeed(
        title="Параллелограмм: признаки и как ими пользоваться",
        description="Учимся не только перечислять признаки, но и понимать, какой из них действительно помогает в доказательстве.",
        initial_prompt="Если в задаче известно, что одна пара противоположных сторон равна и параллельна, почему этого уже может хватить для вывода?",
        difficulty=3,
        tags=["математика", "8класс", "геометрия", "параллелограмм"],
        learning_objectives=[
            {"title": "Выбирает релевантный признак без лишних шагов", "skill_id": "ask_clarifying", "target_level": 45},
            {"title": "Строит доказательство на основе признака", "skill_id": "structure_argument", "target_level": 65},
        ],
    ),
    TopicSeed(
        title="Подобие треугольников: как увидеть отношение, а не форму",
        description="Учимся различать похожесть «на глаз» и математическое подобие с проверяемыми признаками.",
        initial_prompt="Почему двух треугольников недостаточно назвать похожими только потому, что они выглядят одинаково?",
        difficulty=4,
        tags=["математика", "8класс", "геометрия", "подобие"],
        learning_objectives=[
            {"title": "Опровергает интуитивную ошибку контрпримером", "skill_id": "use_counterexample", "target_level": 60},
            {"title": "Задаёт уточняющие вопросы о признаках подобия", "skill_id": "ask_clarifying", "target_level": 50},
        ],
    ),
]


def pick_author_id() -> int:
    with SessionLocal() as db:
        admin = db.execute(select(User).where(User.role == "admin").order_by(User.id.asc())).scalars().first()
        if admin is not None:
            return int(admin.id)
        user = db.execute(select(User).order_by(User.id.asc())).scalars().first()
        if user is None:
            raise RuntimeError("No users found in database; cannot create topics without author")
        return int(user.id)


def upsert_topics() -> tuple[int, int]:
    author_id = pick_author_id()
    created = 0
    updated = 0
    with SessionLocal() as db:
        existing = {
            row.title.strip().lower(): row
            for row in db.execute(select(Topic)).scalars().all()
        }
        for item in TOPICS:
            key = item.title.strip().lower()
            row = existing.get(key)
            payload = {
                "title": item.title.strip(),
                "description": item.description.strip(),
                "initial_prompt": item.initial_prompt.strip(),
                "difficulty": max(1, min(5, int(item.difficulty))),
                "tags": [str(tag).strip().lower() for tag in item.tags if str(tag).strip()],
                "learning_objectives": normalize_learning_objectives(item.learning_objectives),
                "is_premium": False,
                "is_active": True,
                "created_by": author_id,
            }
            if row is None:
                db.add(Topic(**payload))
                created += 1
            else:
                row.description = payload["description"]
                row.initial_prompt = payload["initial_prompt"]
                row.difficulty = payload["difficulty"]
                row.tags = payload["tags"]
                row.learning_objectives = payload["learning_objectives"]
                row.is_premium = payload["is_premium"]
                row.is_active = payload["is_active"]
                updated += 1
        db.commit()
    return created, updated


if __name__ == "__main__":
    created, updated = upsert_topics()
    print(f"seeded topics: created={created} updated={updated} total_input={len(TOPICS)}")
