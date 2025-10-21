"""
AI Agent для SoulMirror с использованием LangGraph и Ollama
"""
import os
import json
import requests
import random
import hashlib
from typing import Dict, Any, List, TypedDict, Annotated
from datetime import datetime, timedelta
from langchain_community.llms import Ollama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages


# Определение состояния агента
class AgentState(TypedDict):
    """Состояние AI агента"""
    messages: Annotated[list, add_messages]
    task_type: str
    user_profile: Dict[str, Any]
    result: Dict[str, Any]


def calculate_zodiac_influence(emotion_level: int, event_description: str = "") -> Dict[str, float]:
    """
    Рассчитывает влияние события на знаки зодиака с учетом контекста

    Args:
        emotion_level: Уровень эмоции (1-10)
        event_description: Описание события для контекста

    Returns:
        dict с влиянием на различные знаки зодиака
    """
    influences = {}
    base_exp = max(10, emotion_level * 5)

    # Анализ контекста события для более точного распределения
    event_lower = event_description.lower()

    # Ключевые слова для разных знаков
    keywords = {
        'aries': ['действие', 'начало', 'инициатива', 'борьба', 'соревнование'],
        'taurus': ['стабильность', 'терпение', 'материальное', 'комфорт', 'упорство'],
        'gemini': ['общение', 'обучение', 'информация', 'любопытство', 'разговор'],
        'cancer': ['семья', 'дом', 'эмоции', 'забота', 'защита'],
        'leo': ['творчество', 'признание', 'лидерство', 'успех', 'выступление'],
        'virgo': ['анализ', 'порядок', 'работа', 'детали', 'помощь'],
        'libra': ['отношения', 'гармония', 'баланс', 'справедливость', 'красота'],
        'scorpio': ['трансформация', 'глубина', 'страсть', 'тайна', 'изменение'],
        'sagittarius': ['путешествие', 'философия', 'свобода', 'приключение', 'знание'],
        'capricorn': ['цель', 'карьера', 'ответственность', 'достижение', 'дисциплина'],
        'aquarius': ['инновация', 'независимость', 'друзья', 'будущее', 'уникальность'],
        'pisces': ['интуиция', 'мечта', 'духовность', 'сострадание', 'искусство']
    }

    # Базовое распределение по эмоциям
    if emotion_level >= 7:  # Позитивные эмоции
        influences = {
            'leo': base_exp * 1.2,
            'sagittarius': base_exp * 1.1,
            'aries': base_exp
        }
    elif emotion_level <= 3:  # Негативные эмоции - возможность роста
        influences = {
            'scorpio': base_exp * 1.2,
            'capricorn': base_exp * 1.1,
            'pisces': base_exp
        }
    else:  # Нейтральные
        influences = {
            'libra': base_exp * 1.1,
            'virgo': base_exp
        }

    # Дополнительное влияние на основе ключевых слов
    for sign, words in keywords.items():
        for word in words:
            if word in event_lower:
                influences[sign] = influences.get(sign, 0) + base_exp * 0.3

    return influences


def generate_tarot_spread(question: str) -> List[Dict[str, str]]:
    """
    Генерирует расклад Таро на основе вопроса

    Args:
        question: Вопрос пользователя

    Returns:
        list карт Таро для расклада
    """
    # Полная колода Таро - 22 старших аркана
    major_arcana = {
        "Шут": "Новые начинания, спонтанность, свобода",
        "Маг": "Мастерство, сила воли, ресурсы",
        "Верховная Жрица": "Интуиция, тайные знания, подсознание",
        "Императрица": "Плодородие, изобилие, забота",
        "Император": "Власть, структура, контроль",
        "Иерофант": "Традиции, духовность, наставничество",
        "Влюбленные": "Выбор, любовь, партнерство",
        "Колесница": "Победа, контроль, движение вперед",
        "Сила": "Внутренняя сила, храбрость, терпение",
        "Отшельник": "Самопознание, уединение, мудрость",
        "Колесо Фортуны": "Судьба, циклы, перемены",
        "Справедливость": "Равновесие, истина, закон",
        "Повешенный": "Новая перспектива, жертва, пауза",
        "Смерть": "Трансформация, окончание, обновление",
        "Умеренность": "Баланс, гармония, модерация",
        "Дьявол": "Материализм, зависимость, искушение",
        "Башня": "Разрушение, откровение, освобождение",
        "Звезда": "Надежда, вдохновение, исцеление",
        "Луна": "Иллюзии, страхи, подсознание",
        "Солнце": "Радость, успех, ясность",
        "Суд": "Возрождение, прощение, призвание",
        "Мир": "Завершение, целостность, достижение"
    }

    # Выбираем карты с учетом контекста вопроса
    question_lower = question.lower()

    # Анализ вопроса для более подходящих карт
    if any(word in question_lower for word in ['любовь', 'отношения', 'партнер']):
        # Для вопросов о любви предпочтительны определенные карты
        preferred = ["Влюбленные", "Императрица", "Солнце", "Звезда"]
    elif any(word in question_lower for word in ['работа', 'карьера', 'деньги', 'финансы']):
        preferred = ["Император", "Колесница", "Солнце", "Колесо Фортуны"]
    elif any(word in question_lower for word in ['изменения', 'перемены', 'будущее']):
        preferred = ["Смерть", "Башня", "Колесо Фортуны", "Суд"]
    elif any(word in question_lower for word in ['духовность', 'развитие', 'познание']):
        preferred = ["Отшельник", "Верховная Жрица", "Иерофант", "Звезда"]
    else:
        preferred = list(major_arcana.keys())

    # Убеждаемся что предпочтительных карт достаточно
    available_cards = list(major_arcana.keys())
    if len(preferred) < 3:
        preferred = available_cards

    # Выбираем 3 карты для расклада
    selected = []
    used_indices = set()

    # 70% вероятность выбрать из предпочтительных карт
    for i in range(3):
        if random.random() < 0.7 and preferred:
            card = random.choice(preferred)
            preferred.remove(card) if card in preferred else None
        else:
            card = random.choice(available_cards)

        selected.append(card)
        available_cards.remove(card) if card in available_cards else None

    return [
        {"position": "Прошлое", "card": selected[0], "meaning": major_arcana[selected[0]]},
        {"position": "Настоящее", "card": selected[1], "meaning": major_arcana[selected[1]]},
        {"position": "Будущее", "card": selected[2], "meaning": major_arcana[selected[2]]}
    ]


class SoulMirrorAgent:
    """
    AI агент с LangGraph для приложения SoulMirror
    """

    def __init__(self, ollama_url: str = None, model: str = "llama2"):
        self.ollama_url = ollama_url or os.getenv("OLLAMA_API_URL", "http://localhost:11434")
        self.model = model

        # Инициализация LLM
        try:
            self.llm = Ollama(base_url=self.ollama_url, model=self.model)
        except:
            self.llm = None
            print(f"Предупреждение: Ollama недоступна на {self.ollama_url}")

        # Создаем граф для разных типов задач
        self.graph = self._create_graph()

    def _create_graph(self) -> StateGraph:
        """Создает граф обработки с LangGraph"""
        workflow = StateGraph(AgentState)

        # Добавляем узлы для разных задач
        workflow.add_node("analyze_context", self._analyze_context)
        workflow.add_node("generate_advice", self._generate_advice_node)
        workflow.add_node("interpret_tarot", self._interpret_tarot_node)
        workflow.add_node("create_task", self._create_task_node)
        workflow.add_node("interpret_natal", self._interpret_natal_node)

        # Добавляем условный роутинг
        workflow.add_conditional_edges(
            START,
            self._route_task,
            {
                "daily_entry": "analyze_context",
                "daily_advice": "generate_advice",
                "tarot": "interpret_tarot",
                "task": "create_task",
                "natal_chart": "interpret_natal"
            }
        )

        # Связываем узлы
        workflow.add_edge("analyze_context", "generate_advice")
        workflow.add_edge("generate_advice", END)
        workflow.add_edge("interpret_tarot", END)
        workflow.add_edge("create_task", END)
        workflow.add_edge("interpret_natal", END)

        return workflow.compile()

    def _route_task(self, state: AgentState) -> str:
        """Определяет тип задачи"""
        return state.get("task_type", "daily_advice")

    def _analyze_context(self, state: AgentState) -> AgentState:
        """Анализирует контекст события"""
        messages = state["messages"]
        user_profile = state["user_profile"]

        # Извлекаем информацию о событии
        event_info = messages[-1].content if messages else ""

        # Добавляем системное сообщение с контекстом
        state["messages"].append(
            SystemMessage(content=f"Пользователь: {user_profile.get('inner_sign', 'неизвестный знак')}, уровень {user_profile.get('level', 1)}")
        )

        return state

    def _generate_advice_node(self, state: AgentState) -> AgentState:
        """Генерирует совет через LLM"""
        messages = state["messages"]

        if self.llm:
            try:
                response = self.llm.invoke(str(messages[-1].content))
                state["result"] = {"advice": response}
            except:
                state["result"] = {"advice": self._get_fallback_response("совет")}
        else:
            state["result"] = {"advice": self._get_fallback_response("совет")}

        return state

    def _interpret_tarot_node(self, state: AgentState) -> AgentState:
        """Интерпретирует расклад Таро"""
        messages = state["messages"]

        if self.llm:
            try:
                response = self.llm.invoke(str(messages[-1].content))
                state["result"] = {"interpretation": response}
            except:
                state["result"] = {"interpretation": self._get_fallback_response("таро")}
        else:
            state["result"] = {"interpretation": self._get_fallback_response("таро")}

        return state

    def _create_task_node(self, state: AgentState) -> AgentState:
        """Создает рекомендацию по задаче"""
        messages = state["messages"]

        if self.llm:
            try:
                response = self.llm.invoke(str(messages[-1].content))
                state["result"] = {"task": response}
            except:
                state["result"] = {"task": self._get_fallback_response("задача")}
        else:
            state["result"] = {"task": self._get_fallback_response("задача")}

        return state

    def _interpret_natal_node(self, state: AgentState) -> AgentState:
        """Интерпретирует натальную карту"""
        messages = state["messages"]

        if self.llm:
            try:
                response = self.llm.invoke(str(messages[-1].content))
                state["result"] = {"natal_interpretation": response}
            except:
                state["result"] = {"natal_interpretation": self._get_fallback_response("натальная карта")}
        else:
            state["result"] = {"natal_interpretation": self._get_fallback_response("натальная карта")}

        return state

    def _sanitize_input(self, text: str) -> str:
        """
        Защита от prompt injection - очищает пользовательский ввод
        """
        if not text or not isinstance(text, str):
            return ""

        # Список опасных паттернов для удаления/замены
        dangerous_patterns = [
            r'(?i)ты\s+[-–—]\s+',  # "Ты - "
            r'(?i)ты\s+теперь\s+',  # "Ты теперь"
            r'(?i)игнорируй\s+',  # "Игнорируй"
            r'(?i)забудь\s+',  # "Забудь"
            r'(?i)system\s*:',  # "system:"
            r'(?i)assistant\s*:',  # "assistant:"
            r'(?i)prompt\s*:',  # "prompt:"
            r'(?i)инструкция\s*:',  # "инструкция:"
            r'(?i)новая\s+роль',  # "новая роль"
            r'(?i)притворись\s+',  # "притворись"
            r'(?i)веди\s+себя\s+как',  # "веди себя как"
            r'(?i)представь\s+что\s+ты',  # "представь что ты"
        ]

        import re
        sanitized = text
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized)

        # Ограничиваем длину
        max_length = 2000
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        return sanitized.strip()

    def _clean_ai_response(self, text: str) -> str:
        """
        Очищает ответ от лишних символов форматирования
        """
        import re

        # Удаляем markdown заголовки (# ## ###)
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

        # Удаляем жирный текст (**текст** или __текст__)
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'__(.+?)__', r'\1', text)

        # Удаляем курсив (*текст* или _текст_)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'_(.+?)_', r'\1', text)

        # Удаляем нумерованные списки в начале строк (1. 2. 3. и т.д.)
        text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)

        # Удаляем маркеры списков (- * +)
        text = re.sub(r'^[-*+]\s+', '', text, flags=re.MULTILINE)

        # Удаляем множественные пробелы
        text = re.sub(r'\s+', ' ', text)

        # Удаляем пробелы в начале и конце
        text = text.strip()

        return text

    def _call_ollama(self, prompt: str, num_predict: int = 512) -> str:
        """Вызывает Ollama API напрямую"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.8,
                        "num_predict": num_predict
                    }
                },
                timeout=90
            )

            if response.status_code == 200:
                result = response.json().get("response", "").strip()
                # Очищаем от лишних символов форматирования
                result = self._clean_ai_response(result)
                return result
            else:
                return self._get_fallback_response(prompt)
        except Exception as e:
            print(f"Ошибка при вызове Ollama: {e}")
            return self._get_fallback_response(prompt)

    def _get_fallback_response(self, context: str) -> str:
        """Возвращает fallback ответ"""
        fallbacks = {
            "событие": "Каждое переживание - это шаг на пути самопознания. Примите свои чувства и используйте этот опыт для внутреннего роста.",
            "совет": "Сегодня звезды советуют прислушаться к своему внутреннему голосу. Доверьтесь интуиции.",
            "таро": "Карты указывают на период трансформации. Будьте открыты новым возможностям и доверьтесь своей мудрости.",
            "задача": "Рекомендация: Исследуйте произведения, которые резонируют с вашей душой."
        }

        for key, value in fallbacks.items():
            if key in context.lower():
                return value

        return "Звезды благосклонны к вашему пути самопознания."

    def process_daily_entry(self, event_description: str, emotion_level: int, user_profile: Dict) -> Dict[str, Any]:
        """
        Обрабатывает ежедневную запись с учетом контекста
        """
        # Анализируем эмоцию с контекстом
        influences = calculate_zodiac_influence(emotion_level, event_description)

        # Определяем эмоциональный контекст
        if emotion_level <= 3:
            emotion_context = "очень сложные, тяжелые переживания"
        elif emotion_level <= 5:
            emotion_context = "негативные, непростые чувства"
        elif emotion_level <= 7:
            emotion_context = "нейтральные, спокойные эмоции"
        else:
            emotion_context = "позитивные, радостные переживания"

        # Защита от prompt injection
        event_description_safe = self._sanitize_input(event_description)
        inner_sign_safe = self._sanitize_input(str(user_profile.get('inner_sign', 'не определен')))

        # Астрологический совет для дневника самопознания
        prompt = f"""Ты - профессиональный астролог. Дай астрологический совет на основе записи клиента.

Знак зодиака: {inner_sign_safe}
Уровень самопознания: {user_profile.get('level', 1)}

Запись из дневника:
"{event_description_safe}"

Эмоциональная оценка: {emotion_level}/10

Дай астрологический совет из 4-5 предложений:
- Как энергия знака {user_profile.get('inner_sign', 'не определен')} проявляется в этой ситуации
- Что говорят звезды о происходящем
- Астрологические рекомендации для работы с ситуацией
- Поддержка и напутствие от космоса

БЕЗ нумерации, маркеров, звездочек, решеток.
Только текст. Профессионально и эмпатично.
Ответь на русском языке."""

        advice = self._call_ollama(prompt)
        base_experience = max(10, emotion_level * 5)

        return {
            "advice": advice,
            "experience_gained": int(base_experience),
            "sign_influences": influences
        }

    def generate_daily_advice(self, user_profile: Dict) -> str:
        """
        Генерирует персонализированный совет дня через LangGraph
        """
        # Защита от prompt injection
        inner_sign = self._sanitize_input(str(user_profile.get('inner_sign', 'Овен')))
        level = user_profile.get('level', 1)
        user_id = user_profile.get('user_id', 'unknown')

        # Добавляем вариативность через случайные темы и стили
        themes = [
            ('самопознание', 'исследуй свой внутренний мир, прислушайся к истинным желаниям'),
            ('отношения', 'обрати внимание на близких, покажи заботу и понимание'),
            ('карьера', 'сосредоточься на целях, прояви свои лучшие качества в работе'),
            ('баланс', 'найди гармонию между делом и отдыхом, позаботься о себе'),
            ('творчество', 'дай волю креативности, попробуй что-то новое')
        ]
        theme_name, theme_action = random.choice(themes)

        prompt = f"""Ты - опытный астролог. Дай короткий вдохновляющий совет на день для знака {inner_sign}.

Тема дня: {theme_name}

Создай совет из 2-3 коротких предложений:
- Что говорят звезды сегодня
- Конкретная рекомендация: {theme_action}

БЕЗ нумерации, заголовков, звездочек, решеток.
Только текст. Просто и по делу.
Ответь на русском языке."""

        # Используем LangGraph для генерации
        try:
            initial_state = {
                "messages": [HumanMessage(content=prompt)],
                "task_type": "daily_advice",
                "user_profile": user_profile,
                "result": {}
            }

            final_state = self.graph.invoke(initial_state)
            return final_state.get("result", {}).get("advice", self._get_fallback_response("совет"))
        except Exception as e:
            print(f"Ошибка при генерации совета через LangGraph: {e}")
            return self._call_ollama(prompt)

    def interpret_tarot_reading(self, question: str, cards: List[Dict], user_profile: Dict = None) -> str:
        """
        Интерпретирует расклад Таро через LangGraph с учетом вопроса
        """
        # Защита от prompt injection
        question_safe = self._sanitize_input(question)

        cards_info = "\n".join([
            f"{c['position']}: {c['card']}"
            for c in cards
        ])

        prompt = f"""Ты - таролог. Проанализируй расклад Таро для вопроса: "{question_safe}"

Карты:
{cards_info}

Дай короткую интерпретацию из 4-5 предложений:

Прошлое ({cards[0]['card']}): Что привело к ситуации.
Настоящее ({cards[1]['card']}): Что происходит сейчас.
Будущее ({cards[2]['card']}): Куда это ведет и что делать.

БЕЗ нумерации, маркеров, звездочек, решеток.
Только текст. Понятно и по делу.
Ответь на русском языке."""

        # Используем LangGraph для интерпретации Таро
        try:
            initial_state = {
                "messages": [HumanMessage(content=prompt)],
                "task_type": "tarot",
                "user_profile": user_profile or {},
                "result": {}
            }

            final_state = self.graph.invoke(initial_state)
            return final_state.get("result", {}).get("interpretation", self._call_ollama(prompt))
        except Exception as e:
            print(f"Ошибка при интерпретации Таро через LangGraph: {e}")
            return self._call_ollama(prompt)

    def generate_task_recommendation(self, user_profile: Dict, target_sign: str, existing_titles: set = None) -> Dict[str, Any]:
        """
        Генерирует персонализированную рекомендацию

        Args:
            user_profile: Профиль пользователя
            target_sign: Целевой знак зодиака
            existing_titles: Множество уже существующих названий (для избежания дубликатов)
        """
        # Защита от prompt injection
        target_sign_safe = self._sanitize_input(str(target_sign))

        # Подготовка списка исключений
        if existing_titles is None:
            existing_titles = set()

        task_types = ['book', 'movie', 'series']
        task_type = random.choice(task_types)

        type_names = {
            'book': 'книгу',
            'movie': 'фильм',
            'series': 'сериал'
        }

        # Множественные аспекты качеств для каждого знака (для разнообразия)
        sign_qualities_variants = {
            'Овен': [
                'лидерство, инициатива, смелость, энергия',
                'решительность, предприимчивость, независимость, конкурентоспособность',
                'храбрость, новаторство, динамичность, прямота',
                'активность, напористость, пионерский дух, самоутверждение'
            ],
            'Телец': [
                'стабильность, терпение, практичность, чувственность',
                'надежность, упорство, материальная безопасность, верность',
                'последовательность, настойчивость, эстетический вкус, земная мудрость',
                'выносливость, комфорт, финансовая грамотность, природная связь'
            ],
            'Близнецы': [
                'коммуникация, любознательность, гибкость, адаптивность',
                'интеллект, общительность, разносторонность, находчивость',
                'красноречие, обучаемость, многозадачность, остроумие',
                'социальность, информированность, логика, вербальные навыки'
            ],
            'Рак': [
                'эмоциональность, забота, интуиция, семейность',
                'чувствительность, защита близких, эмпатия, домашний уют',
                'материнство, сострадание, память о прошлом, душевность',
                'нежность, верность традициям, эмоциональный интеллект, преданность'
            ],
            'Лев': [
                'творчество, щедрость, уверенность, харизма',
                'лидерство, драматизм, самовыражение, великодушие',
                'достоинство, артистизм, благородство, вдохновение',
                'сила воли, яркость, организаторские способности, гордость'
            ],
            'Дева': [
                'аналитичность, внимательность к деталям, служение, совершенство',
                'практичность, критическое мышление, организованность, здоровье',
                'методичность, скромность, полезность, точность',
                'рациональность, трудолюбие, систематизация, забота о других'
            ],
            'Весы': [
                'гармония, дипломатия, справедливость, партнерство',
                'эстетика, баланс, социальные навыки, миротворчество',
                'элегантность, объективность, сотрудничество, искусство компромисса',
                'утонченность, равновесие, культурность, отношения'
            ],
            'Скорпион': [
                'глубина, трансформация, страсть, проницательность',
                'интенсивность, психология, власть, возрождение',
                'магнетизм, исследование тайн, целеустремленность, выживание',
                'решительность, эмоциональная сила, регенерация, контроль'
            ],
            'Стрелец': [
                'оптимизм, философия, стремление к знаниям, приключения',
                'свобода, расширение горизонтов, мудрость, путешествия',
                'идеализм, высшее образование, вера, исследование мира',
                'энтузиазм, истина, международность, духовный рост'
            ],
            'Козерог': [
                'амбициозность, дисциплина, ответственность, достижения',
                'целеустремленность, структура, карьера, профессионализм',
                'выдержка, стратегия, авторитет, долгосрочное планирование',
                'надежность, практицизм, управление, социальный статус'
            ],
            'Водолей': [
                'оригинальность, гуманизм, независимость, инновации',
                'прогрессивность, дружба, интеллектуальность, свобода мысли',
                'индивидуальность, альтруизм, технологии, будущее',
                'нестандартность, коллективное сознание, реформы, эксцентричность'
            ],
            'Рыбы': [
                'сострадание, интуиция, творческое воображение, духовность',
                'чувствительность, мистика, жертвенность, артистизм',
                'эмпатия, мечтательность, универсальная любовь, целительство',
                'тонкость восприятия, вдохновение, растворение границ, экстрасенсорика'
            ]
        }

        # Случайный выбор варианта качеств для разнообразия
        qualities_list = sign_qualities_variants.get(target_sign_safe, ['самопознание'])
        qualities = random.choice(qualities_list)

        # Разные фокусы описания для разнообразия
        description_focus = random.choice([
            'сюжет и персонажи',
            'уроки и выводы',
            'эмоциональное воздействие',
            'практическое применение'
        ])

        # Формируем список исключений для промпта
        exclusions_text = ""
        if existing_titles:
            # Берем последние 10 для компактности промпта
            recent_titles = list(existing_titles)[-10:]
            if recent_titles:
                exclusions_text = f"\n\nНЕ РЕКОМЕНДУЙ ЭТИ ПРОИЗВЕДЕНИЯ (уже были):\n" + "\n".join([f"- {title}" for title in recent_titles])

        prompt = f"""Ты - эксперт по культуре и астрологии. Порекомендуй КОНКРЕТНОЕ произведение.

ТИП КОНТЕНТА: {type_names[task_type]}
ЦЕЛЕВОЙ ЗНАК: {target_sign_safe}
КАЧЕСТВА ДЛЯ РАЗВИТИЯ: {qualities}{exclusions_text}

ЗАДАЧА:
Порекомендуй РЕАЛЬНО СУЩЕСТВУЮЩЕЕ произведение (книгу/фильм/сериал), которое поможет развить качества {target_sign_safe}: {qualities}

ТРЕБОВАНИЯ К РЕКОМЕНДАЦИИ:
- Это должно быть ИЗВЕСТНОЕ произведение (не выдумывай названия!)
- Подходит для развития качеств: {qualities}
- Имеет глубокий смысл или вдохновляющий сюжет
- ВАЖНО: Рекомендуй произведение, которого НЕТ в списке исключений выше!

ПРИМЕРЫ ХОРОШИХ РЕКОМЕНДАЦИЙ:
Для книги: "Алхимик" Пауло Коэльо, "1984" Джорджа Оруэлла
Для фильма: "Форрест Гамп", "Начало", "Интерстеллар"
Для сериала: "Во все тяжкие", "Игра престолов", "Шерлок"

ФОРМАТ ОТВЕТА (СТРОГО СЛЕДУЙ):
Название: [ТОЛЬКО название произведения БЕЗ автора/режиссера]
Автор: [Для книг - автор (максимум 3 автора через запятую). Для фильмов/сериалов - режиссер или "не указано"]
Описание: [2-3 предложения с акцентом на {description_focus}: (1) О чем произведение? (2) Как оно помогает развить качества {target_sign_safe}? (3) Какой конкретный урок можно извлечь?]

ВАЖНО:
- Название должно быть ТОЧНЫМ и РЕАЛЬНО СУЩЕСТВУЮЩИМ
- Описание должно быть конкретным и вдохновляющим
- Объясни СВЯЗЬ между произведением и качествами {target_sign_safe}
- БЕЗ лишнего текста, только формат выше

Ответь на русском языке."""

        response = self._call_ollama(prompt)

        # Улучшенный парсинг ответа
        lines = [line.strip() for line in response.strip().split('\n') if line.strip()]
        title = None
        author = None
        description = None

        description_lines = []
        capture_description = False

        for line in lines:
            if line.startswith("Название:"):
                title = line.replace("Название:", "").strip()
                # Убираем кавычки если есть
                title = title.strip('"').strip("'")
                # Удаляем автора/режиссера из названия если есть
                if '—' in title:
                    title = title.split('—')[0].strip()
                if ' - ' in title and task_type == 'book':
                    # Для книг часто "Название - Автор"
                    title = title.split(' - ')[0].strip()
                # Убираем "Описание:" если оно попало в название
                if 'Описание:' in title:
                    title = title.split('Описание:')[0].strip()
            elif line.startswith("Автор") or line.startswith("Режиссер"):
                # Извлекаем автора
                author = line.split(":", 1)[1].strip() if ":" in line else None
                if author:
                    # Убираем кавычки и лишние символы
                    author = author.strip('"').strip("'")
                    # Ограничиваем до 3 авторов
                    if ',' in author:
                        authors = [a.strip() for a in author.split(',')]
                        author = ', '.join(authors[:3])
            elif line.startswith("Описание:"):
                desc_text = line.replace("Описание:", "").strip()
                if desc_text:
                    description_lines.append(desc_text)
                capture_description = True
            elif capture_description and not line.startswith("Название:") and not line.startswith("Автор") and not line.startswith("Режиссер"):
                # Собираем продолжение описания
                if len(description_lines) < 5:  # Максимум 5 строк
                    description_lines.append(line)

        # Формируем финальные значения
        if not title:
            # Fallback название
            fallback_titles = {
                'book': {
                    'Овен': '"Думай и богатей" Наполеон Хилл',
                    'Телец': '"Маленький принц" Антуан де Сент-Экзюпери',
                    'Близнецы': '"Мастер и Маргарита" Михаил Булгаков',
                    'Рак': '"Гордость и предубеждение" Джейн Остин',
                    'Лев': '"Портрет Дориана Грея" Оскар Уайльд',
                    'Дева': '"Искусство войны" Сунь Цзы',
                    'Весы': '"Алхимик" Пауло Коэльо',
                    'Скорпион': '"Преступление и наказание" Достоевский',
                    'Стрелец': '"Сиддхартха" Герман Гессе',
                    'Козерог': '"Атлант расправил плечи" Айн Рэнд',
                    'Водолей': '"1984" Джордж Оруэлл',
                    'Рыбы': '"Вино из одуванчиков" Рэй Брэдбери'
                },
                'movie': {
                    'Овен': '"Гладиатор"',
                    'Телец': '"Форрест Гамп"',
                    'Близнецы': '"Начало"',
                    'Рак': '"Жизнь прекрасна"',
                    'Лев': '"Король Лев"',
                    'Дева': '"Игры разума"',
                    'Весы': '"Красота по-американски"',
                    'Скорпион': '"Бойцовский клуб"',
                    'Стрелец': '"В диких условиях"',
                    'Козерог': '"Волк с Уолл-стрит"',
                    'Водолей': '"Матрица"',
                    'Рыбы': '"Интерстеллар"'
                },
                'series': {
                    'Овен': '"Игра престолов"',
                    'Телец': '"Друзья"',
                    'Близнецы': '"Шерлок"',
                    'Рак': '"Во все тяжкие"',
                    'Лев': '"Корона"',
                    'Дева': '"Доктор Хаус"',
                    'Весы': '"Безумцы"',
                    'Скорпион': '"Настоящий детектив"',
                    'Стрелец': '"Звездный путь"',
                    'Козерог': '"Карточный домик"',
                    'Водолей': '"Черное зеркало"',
                    'Рыбы': '"Странные дела"'
                }
            }
            title = fallback_titles.get(task_type, {}).get(target_sign, f'Рекомендация для {target_sign}')

        if description_lines:
            # Объединяем все строки описания
            description = ' '.join(description_lines)
            # Ограничиваем длину
            if len(description) > 350:
                description = description[:347] + "..."
        else:
            description = f"Это произведение поможет вам развить качества знака {target_sign}: {qualities}."

        return {
            "task_type": task_type,
            "title": title,
            "author": author if author and author.lower() not in ['не указано', 'неизвестно', ''] else None,
            "description": description,
            "target_sign": target_sign
        }

    def generate_natal_chart(self, birth_date, birth_sign: str) -> Dict[str, Any]:
        """
        Генерирует упрощенную натальную карту на основе даты рождения и знака зодиака
        """
        # Упрощенная система: используем знак зодиака и дату рождения для вариативности
        # В реальной астрологии нужны точные координаты и время рождения

        # Планеты в знаках (упрощенная версия)
        zodiac_signs = ['aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo',
                       'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces']

        sign_index = zodiac_signs.index(birth_sign.lower()) if birth_sign.lower() in zodiac_signs else 0

        # Используем дату рождения для создания уникального смещения домов
        # Это даст разные дома для разных дат, даже при одном знаке зодиака
        birth_hash = (birth_date.year + birth_date.month * 31 + birth_date.day) % 12

        # Генерируем позиции планет с учетом даты рождения
        # Используем дату для вариативности позиций планет
        planet_seed = birth_date.year * 10000 + birth_date.month * 100 + birth_date.day
        random.seed(planet_seed)  # Устанавливаем seed для воспроизводимости

        planets = {
            'Солнце': {'sign': birth_sign, 'house': 1, 'degree': random.randint(0, 29)},
            'Луна': {'sign': zodiac_signs[(sign_index + random.randint(3, 5)) % 12], 'house': random.randint(1, 12), 'degree': random.randint(0, 29)},
            'Меркурий': {'sign': zodiac_signs[(sign_index + random.choice([-1, 0, 1])) % 12], 'house': random.randint(1, 12), 'degree': random.randint(0, 29)},
            'Венера': {'sign': zodiac_signs[(sign_index + random.choice([-2, -1, 0, 1, 2])) % 12], 'house': random.randint(1, 12), 'degree': random.randint(0, 29)},
            'Марс': {'sign': zodiac_signs[(sign_index + random.randint(0, 11)) % 12], 'house': random.randint(1, 12), 'degree': random.randint(0, 29)},
            'Юпитер': {'sign': zodiac_signs[(sign_index + random.randint(0, 11)) % 12], 'house': random.randint(1, 12), 'degree': random.randint(0, 29)},
            'Сатурн': {'sign': zodiac_signs[(sign_index + random.randint(0, 11)) % 12], 'house': random.randint(1, 12), 'degree': random.randint(0, 29)},
        }

        # Сбрасываем seed для последующих случайных генераций
        random.seed()

        # Дома со знаками - используем birth_hash для уникального распределения
        houses = {}
        for i in range(1, 13):
            # Комбинируем sign_index и birth_hash для уникальности
            house_sign_index = (sign_index + birth_hash + i - 1) % 12
            houses[str(i)] = zodiac_signs[house_sign_index]

        return {
            'planets': planets,
            'houses': houses,
            'aspects': []
        }

    def interpret_natal_chart(self, birth_sign: str, planets: Dict, user_profile: Dict) -> Dict[str, str]:
        """
        Создает AI интерпретацию натальной карты
        """
        planets_info = "\n".join([
            f"- {planet}: в знаке {data['sign']}, {data['house']} дом"
            for planet, data in planets.items()
        ])

        # Общая интерпретация
        general_prompt = f"""Ты - астролог. Опиши личность по натальной карте.

Натальная карта:
- Солнце в {birth_sign}
- Луна в {planets['Луна']['sign']}
- Меркурий в {planets['Меркурий']['sign']}
- Венера в {planets['Венера']['sign']}
- Марс в {planets['Марс']['sign']}

Дай целостный портрет из 6-7 предложений:
- Характер и сильные стороны (Солнце)
- Эмоции и потребности (Луна)
- Мышление и общение (Меркурий)
- Любовь и ценности (Венера)
- Энергия и действия (Марс)

БЕЗ нумерации, маркеров, звездочек, решеток.
Только текст. Конкретно и понятно.
Ответь на русском языке."""

        general_interpretation = self._call_ollama(general_prompt, num_predict=800)

        # Карьера
        career_prompt = f"""Ты - карьерный астролог. Раскрой профессиональный потенциал.

Натальная карта:
- Солнце в {birth_sign}
- Марс в {planets['Марс']['sign']}
- Юпитер в {planets['Юпитер']['sign']}
- Сатурн в {planets['Сатурн']['sign']}

Дай карьерный анализ из 5-6 предложений:
- Природные таланты и сильные стороны (Солнце)
- Стиль работы и энергия (Марс)
- Направления роста и удачи (Юпитер)
- Путь к успеху и уроки (Сатурн)

Назови конкретные профессии и сферы.
БЕЗ нумерации, маркеров, звездочек, решеток.
Только текст. Практично и понятно.
Ответь на русском языке."""

        career_reading = self._call_ollama(career_prompt, num_predict=800)

        # Отношения
        relationships_prompt = f"""Ты - астролог по отношениям. Раскрой любовную сферу.

Натальная карта:
- Солнце в {birth_sign}
- Луна в {planets['Луна']['sign']}
- Венера в {planets['Венера']['sign']}
- Марс в {planets['Марс']['sign']}

Дай анализ отношений из 5-6 предложений:
- Стиль любви и притяжение (Венера)
- Эмоциональные потребности (Луна)
- Что важно в партнере (Солнце + Венера)
- Страсть и желания (Марс)

БЕЗ нумерации, маркеров, звездочек, решеток.
Только текст. Честно и понятно.
Ответь на русском языке."""

        relationships_reading = self._call_ollama(relationships_prompt, num_predict=800)

        # Жизненное предназначение
        purpose_prompt = f"""Ты - духовный астролог. Раскрой предназначение души.

Натальная карта:
- Солнце в {birth_sign}
- Луна в {planets['Луна']['sign']}
- Юпитер в {planets['Юпитер']['sign']}
- Сатурн в {planets['Сатурн']['sign']}

Дай вдохновляющий анализ из 5-6 предложений:
- Миссия души (Солнце в {birth_sign})
- Таланты и дары
- Путь развития (Юпитер)
- Кармические уроки (Сатурн)

БЕЗ нумерации, маркеров, звездочек, решеток.
Только текст. Вдохновляюще и понятно.
Ответь на русском языке."""

        life_purpose_reading = self._call_ollama(purpose_prompt, num_predict=800)

        return {
            'interpretation': general_interpretation,
            'career_reading': career_reading,
            'relationships_reading': relationships_reading,
            'life_purpose_reading': life_purpose_reading
        }
