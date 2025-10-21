"""
Кастомные фильтры для форматирования AI ответов
"""
from django import template
import re

register = template.Library()


@register.filter(name='format_ai_text')
def format_ai_text(text):
    """
    Форматирует текст от AI, разбивая на абзацы и добавляя структуру
    """
    if not text:
        return ""

    # Удаляем лишние пробелы и переносы строк
    text = text.strip()

    # Разбиваем на предложения
    sentences = re.split(r'(?<=[.!?])\s+', text)

    # Группируем по 2-3 предложения в абзац
    paragraphs = []
    current_paragraph = []

    for i, sentence in enumerate(sentences):
        current_paragraph.append(sentence)

        # Создаем абзац каждые 2-3 предложения
        if len(current_paragraph) >= 2 and (i == len(sentences) - 1 or len(current_paragraph) >= 3):
            paragraphs.append(' '.join(current_paragraph))
            current_paragraph = []

    # Добавляем остаток, если есть
    if current_paragraph:
        paragraphs.append(' '.join(current_paragraph))

    # Формируем HTML с абзацами
    formatted = ''.join([f'<p class="ai-paragraph">{p}</p>' for p in paragraphs])

    return formatted


@register.filter(name='highlight_keywords')
def highlight_keywords(text):
    """
    Выделяет ключевые астрологические термины
    """
    if not text:
        return ""

    keywords = [
        'Солнце', 'Луна', 'Меркурий', 'Венера', 'Марс', 'Юпитер', 'Сатурн',
        'Овен', 'Телец', 'Близнецы', 'Рак', 'Лев', 'Дева',
        'Весы', 'Скорпион', 'Стрелец', 'Козерог', 'Водолей', 'Рыбы'
    ]

    result = text
    for keyword in keywords:
        # Подсветка только целых слов
        pattern = r'\b(' + re.escape(keyword) + r')\b'
        result = re.sub(pattern, r'<span class="keyword-highlight">\1</span>', result, flags=re.IGNORECASE)

    return result
