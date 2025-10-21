from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, ZodiacSign, ZodiacProfile, DailyEntry, DailyAdvice,
    Task, TarotReading, QuizQuestion, QuizAnswer
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'level', 'total_experience', 'completed_initial_quiz']
    list_filter = ['completed_initial_quiz', 'level']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Игровой профиль', {'fields': ('total_experience', 'level', 'completed_initial_quiz')}),
    )


@admin.register(ZodiacSign)
class ZodiacSignAdmin(admin.ModelAdmin):
    list_display = ['get_name_display', 'name']
    search_fields = ['name']


@admin.register(ZodiacProfile)
class ZodiacProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'birth_sign', 'inner_sign', 'created_at']
    list_filter = ['inner_sign', 'birth_sign']
    search_fields = ['user__username']


@admin.register(DailyEntry)
class DailyEntryAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'emotion_level', 'experience_gained']
    list_filter = ['date', 'emotion_level']
    search_fields = ['user__username', 'event_description']
    date_hierarchy = 'date'


@admin.register(DailyAdvice)
class DailyAdviceAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'is_revealed']
    list_filter = ['date', 'is_revealed']
    search_fields = ['user__username']
    date_hierarchy = 'date'


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['user', 'task_type', 'title', 'target_sign', 'status', 'experience_reward']
    list_filter = ['task_type', 'status', 'target_sign']
    search_fields = ['user__username', 'title']


@admin.register(TarotReading)
class TarotReadingAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'question']
    search_fields = ['user__username', 'question']
    date_hierarchy = 'created_at'


class QuizAnswerInline(admin.TabularInline):
    model = QuizAnswer
    extra = 4


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ['order', 'question_text']
    ordering = ['order']
    inlines = [QuizAnswerInline]


@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    list_display = ['question', 'answer_text']
    search_fields = ['answer_text']
