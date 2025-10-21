from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
import json


class User(AbstractUser):
    """Расширенная модель пользователя"""
    total_experience = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    completed_initial_quiz = models.BooleanField(default=False)

    def __str__(self):
        return self.username


class ZodiacSign(models.Model):
    """Знаки зодиака"""
    SIGNS = [
        ('aries', 'Овен'),
        ('taurus', 'Телец'),
        ('gemini', 'Близнецы'),
        ('cancer', 'Рак'),
        ('leo', 'Лев'),
        ('virgo', 'Дева'),
        ('libra', 'Весы'),
        ('scorpio', 'Скорпион'),
        ('sagittarius', 'Стрелец'),
        ('capricorn', 'Козерог'),
        ('aquarius', 'Водолей'),
        ('pisces', 'Рыбы'),
    ]

    name = models.CharField(max_length=20, choices=SIGNS, unique=True)
    description = models.TextField()
    traits = models.JSONField(default=list)  # Ключевые черты

    def __str__(self):
        return self.get_name_display()


class ZodiacProfile(models.Model):
    """Профиль зодиака пользователя с системой уровней"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='zodiac_profile')
    birth_sign = models.ForeignKey(ZodiacSign, on_delete=models.SET_NULL, null=True, related_name='birth_profiles')
    inner_sign = models.ForeignKey(ZodiacSign, on_delete=models.SET_NULL, null=True, related_name='inner_profiles')

    # Опыт каждого знака зодиака (JSON: {sign_name: experience_points})
    sign_experience = models.JSONField(default=dict)

    # Уровни каждого знака зодиака (JSON: {sign_name: level})
    sign_levels = models.JSONField(default=dict)

    # Старая система прогресса - оставляем для обратной совместимости
    sign_progress = models.JSONField(default=dict)

    # Ответы на начальный опросник
    quiz_answers = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Константы для системы уровней
    XP_PER_LEVEL = 500  # Опыт для следующего уровня
    SIGN_CHANGE_THRESHOLD = 3  # Минимальная разница в уровнях для смены знака

    def __str__(self):
        return f"{self.user.username} - {self.inner_sign}"

    def get_sign_level(self, sign_name: str) -> int:
        """Получить уровень конкретного знака"""
        return self.sign_levels.get(sign_name, 1)

    def get_sign_experience(self, sign_name: str) -> int:
        """Получить опыт конкретного знака"""
        return self.sign_experience.get(sign_name, 0)

    def add_sign_experience(self, sign_name: str, experience: int) -> dict:
        """
        Добавить опыт знаку и проверить повышение уровня
        Возвращает словарь с информацией о изменениях
        """
        current_exp = self.get_sign_experience(sign_name)
        current_level = self.get_sign_level(sign_name)

        new_exp = current_exp + experience
        self.sign_experience[sign_name] = new_exp

        # Проверяем повышение уровня
        levels_gained = 0
        while new_exp >= self.XP_PER_LEVEL:
            new_exp -= self.XP_PER_LEVEL
            current_level += 1
            levels_gained += 1

        self.sign_experience[sign_name] = new_exp
        self.sign_levels[sign_name] = current_level

        return {
            'sign': sign_name,
            'new_level': current_level,
            'levels_gained': levels_gained,
            'current_exp': new_exp,
            'exp_to_next_level': self.XP_PER_LEVEL
        }

    def get_dominant_sign(self) -> str:
        """Определяет доминирующий знак по уровню"""
        if not self.sign_levels:
            return self.birth_sign.name if self.birth_sign else 'aries'

        # Находим знак с максимальным уровнем
        max_sign = max(self.sign_levels.items(), key=lambda x: x[1])
        return max_sign[0]

    def check_sign_change(self) -> tuple[bool, str]:
        """
        Проверяет, нужно ли сменить внутренний знак
        Возвращает (нужна_смена, новый_знак)
        """
        if not self.sign_levels or not self.inner_sign:
            return False, None

        dominant_sign = self.get_dominant_sign()
        current_sign = self.inner_sign.name

        # Если это разные знаки
        if dominant_sign != current_sign:
            dominant_level = self.get_sign_level(dominant_sign)
            current_level = self.get_sign_level(current_sign)

            # Смена происходит только если разница >= SIGN_CHANGE_THRESHOLD
            if dominant_level - current_level >= self.SIGN_CHANGE_THRESHOLD:
                return True, dominant_sign

        return False, None

    def get_all_sign_stats(self) -> list:
        """Получить статистику по всем знакам для отображения"""
        stats = []
        all_signs = ZodiacSign.SIGNS

        for sign_code, sign_name in all_signs:
            level = self.get_sign_level(sign_code)
            exp = self.get_sign_experience(sign_code)
            stats.append({
                'code': sign_code,
                'name': sign_name,
                'level': level,
                'experience': exp,
                'progress_percent': int((exp / self.XP_PER_LEVEL) * 100),
                'is_current': self.inner_sign and self.inner_sign.name == sign_code
            })

        # Сортируем по уровню (от большего к меньшему)
        stats.sort(key=lambda x: (x['level'], x['experience']), reverse=True)
        return stats


class DailyEntry(models.Model):
    """Ежедневные записи пользователя"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_entries')
    date = models.DateField(auto_now_add=True)
    event_description = models.TextField()
    emotion_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="От 1 (худшая) до 10 (лучшая)"
    )

    # AI анализ и совет
    ai_advice = models.TextField(blank=True)
    experience_gained = models.IntegerField(default=0)
    sign_influences = models.JSONField(default=dict)  # Влияние на знаки зодиака

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Daily Entries"
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.date}"


class DailyAdvice(models.Model):
    """Ежедневный совет от ИИ"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_advices')
    date = models.DateField(auto_now_add=True)
    advice = models.TextField()
    is_revealed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['user', 'date']

    def __str__(self):
        return f"{self.user.username} - {self.date}"


class Task(models.Model):
    """Задания для пользователей (книги, фильмы, сериалы)"""
    TASK_TYPES = [
        ('book', 'Книга'),
        ('movie', 'Фильм'),
        ('series', 'Сериал'),
    ]

    STATUS_CHOICES = [
        ('assigned', 'Назначено'),
        ('in_progress', 'В процессе'),
        ('completed', 'Выполнено'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    task_type = models.CharField(max_length=10, choices=TASK_TYPES)
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField()
    target_sign = models.ForeignKey(ZodiacSign, on_delete=models.SET_NULL, null=True)

    # Метаданные из интернета
    external_data = models.JSONField(default=dict)

    experience_reward = models.IntegerField(default=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='assigned')

    assigned_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-assigned_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', '-completed_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_task_type_display()}: {self.title}"


class TarotReading(models.Model):
    """Расклады Таро"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tarot_readings')
    question = models.TextField()

    # Карты расклада (JSON массив)
    cards = models.JSONField(default=list)

    # Интерпретация от ИИ
    interpretation = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.created_at.date()}"


class NatalChart(models.Model):
    """Натальная карта пользователя"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='natal_charts')

    # Базовая информация для построения карты
    birth_date = models.DateField()
    birth_time = models.TimeField(null=True, blank=True)
    birth_place = models.CharField(max_length=255, blank=True)

    # Знаки в домах (JSON: {house_number: sign_name})
    houses = models.JSONField(default=dict)

    # Позиции планет (JSON: {planet_name: {sign: ..., house: ..., degree: ...}})
    planets = models.JSONField(default=dict)

    # Аспекты (JSON: [{planet1: ..., planet2: ..., aspect_type: ..., orb: ...}])
    aspects = models.JSONField(default=list)

    # AI интерпретация натальной карты
    interpretation = models.TextField()

    # Детальная интерпретация по разделам
    personality_reading = models.TextField(blank=True)
    career_reading = models.TextField(blank=True)
    relationships_reading = models.TextField(blank=True)
    life_purpose_reading = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Натальная карта"
        verbose_name_plural = "Натальные карты"

    def __str__(self):
        return f"Натальная карта {self.user.username} ({self.birth_date})"


class QuizQuestion(models.Model):
    """Вопросы астрологического опросника"""
    question_text = models.TextField()
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}"


class QuizAnswer(models.Model):
    """Варианты ответов на вопросы"""
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.CharField(max_length=255)

    # Влияние на знаки зодиака (JSON: {sign_name: weight})
    sign_weights = models.JSONField(default=dict)

    def __str__(self):
        return self.answer_text
