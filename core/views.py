from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import date, timedelta
from django.views.decorators.http import require_http_methods
import json
import random

from .models import (
    User, ZodiacSign, ZodiacProfile, DailyEntry, DailyAdvice,
    Task, TarotReading, QuizQuestion, QuizAnswer, NatalChart
)
from .ai.agent import SoulMirrorAgent
from django.conf import settings


# Инициализация AI агента
ai_agent = SoulMirrorAgent(
    ollama_url=settings.OLLAMA_API_URL,
    model=settings.OLLAMA_MODEL
)


def _ensure_user_has_tasks(user, profile):
    """
    Проверяет и создает задания для пользователя ТОЛЬКО для текущего знака
    """
    # Проверяем есть ли активные задания для текущего знака
    current_sign = profile.inner_sign
    if not current_sign:
        return

    active_tasks_count = Task.objects.filter(
        user=user,
        status__in=['assigned', 'in_progress'],
        target_sign=current_sign
    ).count()

    # Если меньше 3 активных заданий для текущего знака, создаем новые
    if active_tasks_count < 3:
        try:
            # Генерируем рекомендацию ТОЛЬКО для текущего знака
            current_sign_level = profile.get_sign_level(current_sign.name)

            user_profile_data = {
                'inner_sign': current_sign.get_name_display(),
                'level': user.level,
                'experience': user.total_experience,
                'sign_level': current_sign_level
            }

            # Получаем список всех уже существующих заданий пользователя (включая выполненные)
            existing_titles = set(Task.objects.filter(user=user).values_list('title', flat=True))

            # Пытаемся сгенерировать уникальное задание (максимум 5 попыток)
            max_attempts = 5
            for attempt in range(max_attempts):
                recommendation = ai_agent.generate_task_recommendation(
                    user_profile_data,
                    current_sign.get_name_display(),
                    existing_titles
                )

                # Проверяем, что такого задания еще нет
                if recommendation['title'] not in existing_titles:
                    # Создаем задание для текущего знака
                    Task.objects.create(
                        user=user,
                        task_type=recommendation['task_type'],
                        title=recommendation['title'],
                        author=recommendation.get('author'),
                        description=recommendation['description'],
                        target_sign=current_sign,
                        experience_reward=random.randint(100, 200),  # Увеличен опыт
                        status='assigned'
                    )
                    break  # Успешно создали уникальное задание
                elif attempt == max_attempts - 1:
                    # Если после 5 попыток не удалось создать уникальное - создаем любое
                    print(f"Предупреждение: Не удалось создать уникальное задание за {max_attempts} попыток")
                    Task.objects.create(
                        user=user,
                        task_type=recommendation['task_type'],
                        title=recommendation['title'],
                        author=recommendation.get('author'),
                        description=recommendation['description'],
                        target_sign=current_sign,
                        experience_reward=random.randint(100, 200),
                        status='assigned'
                    )
        except Exception as e:
            print(f"Ошибка при создании задания: {e}")


def _cleanup_old_tasks(user, new_sign):
    """
    Удаляет незавершенные задания при смене знака
    """
    # Удаляем все незавершенные задания, которые НЕ относятся к новому знаку
    deleted_count = Task.objects.filter(
        user=user,
        status__in=['assigned', 'in_progress']
    ).exclude(
        target_sign__name=new_sign
    ).delete()

    return deleted_count[0] if deleted_count else 0


def register_view(request):
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        if password != password_confirm:
            return render(request, 'core/register.html', {
                'error': 'Пароли не совпадают'
            })

        if User.objects.filter(username=username).exists():
            return render(request, 'core/register.html', {
                'error': 'Пользователь с таким именем уже существует'
            })

        user = User.objects.create_user(username=username, password=password)
        login(request, user)
        return redirect('quiz')

    return render(request, 'core/register.html')


def login_view(request):
    """Авторизация пользователя"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            # Проверяем, прошел ли пользователь опросник
            if not user.completed_initial_quiz:
                return redirect('quiz')
            return redirect('dashboard')
        else:
            return render(request, 'core/login.html', {
                'error': 'Неверное имя пользователя или пароль'
            })

    return render(request, 'core/login.html')


def logout_view(request):
    """Выход из системы"""
    logout(request)
    return redirect('login')


@login_required
def quiz_view(request):
    """Астрологический опросник для определения внутреннего знака"""
    if request.user.completed_initial_quiz:
        return redirect('dashboard')

    questions = QuizQuestion.objects.all().prefetch_related('answers')

    if request.method == 'POST':
        # Собираем ответы
        answers = {}
        sign_scores = {sign[0]: 0 for sign in ZodiacSign.SIGNS}

        for question in questions:
            answer_id = request.POST.get(f'question_{question.id}')
            if answer_id:
                answer = QuizAnswer.objects.get(id=answer_id)
                answers[question.id] = answer_id

                # Добавляем веса к знакам
                for sign, weight in answer.sign_weights.items():
                    sign_scores[sign] = sign_scores.get(sign, 0) + weight

        # Определяем внутренний знак
        inner_sign_name = max(sign_scores.items(), key=lambda x: x[1])[0]
        inner_sign = ZodiacSign.objects.get(name=inner_sign_name)

        # Получаем знак рождения из ответов
        birth_sign_answer = request.POST.get('birth_sign')
        birth_sign = ZodiacSign.objects.get(name=birth_sign_answer) if birth_sign_answer else None

        # Создаем профиль зодиака
        profile, created = ZodiacProfile.objects.get_or_create(user=request.user)
        profile.birth_sign = birth_sign
        profile.inner_sign = inner_sign
        profile.quiz_answers = answers
        profile.sign_progress = {sign[0]: sign_scores.get(sign[0], 0) for sign in ZodiacSign.SIGNS}
        profile.save()

        # Отмечаем опросник как пройденный
        request.user.completed_initial_quiz = True
        request.user.save()

        return redirect('dashboard')

    zodiac_signs = ZodiacSign.objects.all()
    return render(request, 'core/quiz.html', {
        'questions': questions,
        'zodiac_signs': zodiac_signs
    })


@login_required
def dashboard_view(request):
    """Главная страница"""
    # Проверяем прошел ли пользователь опросник
    if not request.user.completed_initial_quiz:
        return redirect('quiz')

    try:
        profile = ZodiacProfile.objects.get(user=request.user)
    except ZodiacProfile.DoesNotExist:
        # Если профиль не найден, редиректим на опросник
        return redirect('quiz')

    # Генерируем персональный совет через AI один раз в день
    today = date.today()
    try:
        daily_advice = DailyAdvice.objects.get(user=request.user, date=today)
    except DailyAdvice.DoesNotExist:
        # Создаем совет через AI только если его еще нет сегодня
        advice_text = ai_agent.generate_daily_advice({
            'inner_sign': profile.inner_sign.get_name_display() if profile.inner_sign else 'Овен',
            'level': request.user.level,
            'experience': request.user.total_experience,
            'user_id': request.user.id
        })
        daily_advice = DailyAdvice.objects.create(
            user=request.user,
            date=today,
            advice=advice_text
        )

    # Получаем последние 3 записи для главной страницы
    recent_entries = DailyEntry.objects.filter(user=request.user).order_by('-created_at')[:3]

    # Получаем 3 активных задания для главной страницы
    active_tasks = Task.objects.filter(
        user=request.user,
        status__in=['assigned', 'in_progress']
    ).select_related('target_sign')[:3]

    context = {
        'profile': profile,
        'daily_advice': daily_advice,
        'recent_entries': recent_entries,
        'active_tasks': active_tasks,
        'user': request.user
    }

    return render(request, 'core/dashboard.html', context)


@login_required
@require_http_methods(["POST"])
def reveal_advice_view(request):
    """Открывает ежедневный совет"""
    today = date.today()
    advice = DailyAdvice.objects.get(user=request.user, date=today)
    advice.is_revealed = True
    advice.save()

    return JsonResponse({
        'success': True,
        'advice': advice.advice
    })


@login_required
def daily_entry_view(request):
    """Создание ежедневной записи"""
    if request.method == 'POST':
        event_description = request.POST.get('event_description')
        emotion_level = int(request.POST.get('emotion_level'))

        try:
            profile = ZodiacProfile.objects.get(user=request.user)
        except ZodiacProfile.DoesNotExist:
            return redirect('quiz')

        # Обрабатываем запись через AI
        result = ai_agent.process_daily_entry(
            event_description=event_description,
            emotion_level=emotion_level,
            user_profile={
                'inner_sign': profile.inner_sign.get_name_display() if profile.inner_sign else 'не определен',
                'level': request.user.level,
                'experience': request.user.total_experience
            }
        )

        # Создаем запись
        entry = DailyEntry.objects.create(
            user=request.user,
            event_description=event_description,
            emotion_level=emotion_level,
            ai_advice=result['advice'],
            experience_gained=result['experience_gained'],
            sign_influences=result['sign_influences']
        )

        # Обновляем опыт пользователя
        request.user.total_experience += result['experience_gained']

        # Проверяем повышение уровня
        new_level = (request.user.total_experience // 100) + 1
        if new_level > request.user.level:
            request.user.level = new_level

        request.user.save()

        # Обновляем прогресс знаков зодиака
        for sign, points in result['sign_influences'].items():
            profile.sign_progress[sign] = profile.sign_progress.get(sign, 0) + points

        # Проверяем, не изменился ли внутренний знак
        closest_sign_name = max(profile.sign_progress.items(), key=lambda x: x[1])[0]
        if closest_sign_name != profile.inner_sign.name:
            profile.inner_sign = ZodiacSign.objects.get(name=closest_sign_name)

        profile.save()

        return render(request, 'core/daily_entry_result.html', {
            'entry': entry,
            'experience_gained': result['experience_gained']
        })

    return render(request, 'core/daily_entry.html')


@login_required
def entries_history_view(request):
    """История записей дневника"""
    # Получаем все записи пользователя с пагинацией
    entries = DailyEntry.objects.filter(user=request.user).order_by('-created_at')

    context = {
        'entries': entries,
        'user': request.user
    }

    return render(request, 'core/entries_history.html', context)


@login_required
def tasks_view(request):
    """Просмотр заданий"""
    # Оптимизированные запросы с select_related
    assigned_tasks = Task.objects.filter(
        user=request.user,
        status='assigned'
    ).select_related('target_sign')

    in_progress_tasks = Task.objects.filter(
        user=request.user,
        status='in_progress'
    ).select_related('target_sign')

    completed_tasks = Task.objects.filter(
        user=request.user,
        status='completed'
    ).select_related('target_sign').order_by('-completed_at')[:10]  # Только последние 10

    # Проверяем, нужно ли создать новые задания (только на странице заданий)
    active_count = assigned_tasks.count() + in_progress_tasks.count()
    if active_count < 2:
        try:
            profile = ZodiacProfile.objects.get(user=request.user)
            _ensure_user_has_tasks(request.user, profile)
            # Перезагружаем задания после создания
            assigned_tasks = Task.objects.filter(
                user=request.user,
                status='assigned'
            ).select_related('target_sign')
        except ZodiacProfile.DoesNotExist:
            pass

    context = {
        'assigned_tasks': assigned_tasks,
        'in_progress_tasks': in_progress_tasks,
        'completed_tasks': completed_tasks
    }

    return render(request, 'core/tasks.html', context)


@login_required
@require_http_methods(["POST"])
def start_task_view(request, task_id):
    """Начать выполнение задания"""
    task = get_object_or_404(Task, id=task_id, user=request.user)

    if task.status == 'assigned':
        task.status = 'in_progress'
        task.save()

    return JsonResponse({'success': True})


@login_required
@require_http_methods(["POST"])
def complete_task_view(request, task_id):
    """Отметить задание как выполненное"""
    task = get_object_or_404(Task, id=task_id, user=request.user)

    task.status = 'completed'
    task.completed_at = timezone.now()
    task.save()

    # Добавляем общий опыт пользователю
    request.user.total_experience += task.experience_reward
    new_level = (request.user.total_experience // 100) + 1
    user_leveled_up = False
    if new_level > request.user.level:
        request.user.level = new_level
        user_leveled_up = True
    request.user.save()

    # Новая система уровней знаков
    sign_level_up = False
    sign_changed = False
    new_sign_name = None
    old_tasks_removed = 0

    if task.target_sign:
        try:
            profile = ZodiacProfile.objects.get(user=request.user)

            # Добавляем опыт знаку зодиака
            sign_result = profile.add_sign_experience(
                task.target_sign.name,
                task.experience_reward
            )

            sign_level_up = sign_result['levels_gained'] > 0

            # Проверяем смену знака
            should_change, new_sign = profile.check_sign_change()
            if should_change:
                old_sign = profile.inner_sign.name
                profile.inner_sign = ZodiacSign.objects.get(name=new_sign)
                sign_changed = True
                new_sign_name = profile.inner_sign.get_name_display()

                # Удаляем старые задания
                old_tasks_removed = _cleanup_old_tasks(request.user, new_sign)

            profile.save()
        except ZodiacProfile.DoesNotExist:
            pass  # Профиль будет создан при прохождении опросника

    response_data = {
        'success': True,
        'experience_gained': task.experience_reward,
        'user_leveled_up': user_leveled_up,
        'new_user_level': request.user.level,
        'sign_level_up': sign_level_up,
        'sign_changed': sign_changed,
        'new_sign_name': new_sign_name,
        'old_tasks_removed': old_tasks_removed
    }

    return JsonResponse(response_data)


@login_required
def tarot_view(request):
    """Расклад Таро с AI интерпретацией через LangGraph"""
    if request.method == 'POST':
        question = request.POST.get('question')

        # Генерируем расклад
        from .ai.agent import generate_tarot_spread
        cards = generate_tarot_spread(question)

        # Получаем профиль для персонализации
        try:
            profile = ZodiacProfile.objects.get(user=request.user)
            user_profile = {
                'inner_sign': profile.inner_sign.get_name_display() if profile.inner_sign else 'Овен',
                'level': request.user.level,
                'user_id': request.user.id
            }
        except ZodiacProfile.DoesNotExist:
            user_profile = {
                'level': request.user.level,
                'user_id': request.user.id
            }

        # Получаем интерпретацию от AI через LangGraph
        interpretation = ai_agent.interpret_tarot_reading(question, cards, user_profile)

        # Сохраняем расклад
        reading = TarotReading.objects.create(
            user=request.user,
            question=question,
            cards=cards,
            interpretation=interpretation
        )

        return render(request, 'core/tarot_result.html', {
            'reading': reading
        })

    # История раскладов
    readings = TarotReading.objects.filter(user=request.user).order_by('-created_at')[:10]

    return render(request, 'core/tarot.html', {
        'readings': readings
    })


@login_required
def natal_chart_view(request):
    """Натальная карта"""
    try:
        profile = ZodiacProfile.objects.get(user=request.user)
    except ZodiacProfile.DoesNotExist:
        return redirect('quiz')

    # Проверяем есть ли уже натальная карта
    existing_chart = NatalChart.objects.filter(user=request.user).first()

    if request.method == 'POST':
        birth_date_str = request.POST.get('birth_date')
        birth_time_str = request.POST.get('birth_time')
        birth_place = request.POST.get('birth_place', '')

        # Парсим дату
        from datetime import datetime
        birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
        birth_time = None
        if birth_time_str:
            try:
                birth_time = datetime.strptime(birth_time_str, '%H:%M').time()
            except:
                pass

        # Генерируем натальную карту
        birth_sign = profile.birth_sign.name if profile.birth_sign else 'aries'
        chart_data = ai_agent.generate_natal_chart(birth_date, birth_sign)

        # Получаем интерпретацию от AI
        interpretations = ai_agent.interpret_natal_chart(
            birth_sign=profile.birth_sign.get_name_display() if profile.birth_sign else 'Овен',
            planets=chart_data['planets'],
            user_profile={
                'inner_sign': profile.inner_sign.get_name_display() if profile.inner_sign else 'Овен',
                'level': request.user.level
            }
        )

        # Сохраняем или обновляем натальную карту
        if existing_chart:
            existing_chart.birth_date = birth_date
            existing_chart.birth_time = birth_time
            existing_chart.birth_place = birth_place
            existing_chart.houses = chart_data['houses']
            existing_chart.planets = chart_data['planets']
            existing_chart.aspects = chart_data['aspects']
            existing_chart.interpretation = f"Натальная карта для {profile.birth_sign.get_name_display() if profile.birth_sign else 'человека'}"
            existing_chart.personality_reading = interpretations['interpretation']
            existing_chart.career_reading = interpretations['career_reading']
            existing_chart.relationships_reading = interpretations['relationships_reading']
            existing_chart.life_purpose_reading = interpretations['life_purpose_reading']
            existing_chart.save()
            natal_chart = existing_chart
        else:
            natal_chart = NatalChart.objects.create(
                user=request.user,
                birth_date=birth_date,
                birth_time=birth_time,
                birth_place=birth_place,
                houses=chart_data['houses'],
                planets=chart_data['planets'],
                aspects=chart_data['aspects'],
                interpretation=f"Натальная карта для {profile.birth_sign.get_name_display() if profile.birth_sign else 'человека'}",
                personality_reading=interpretations['interpretation'],
                career_reading=interpretations['career_reading'],
                relationships_reading=interpretations['relationships_reading'],
                life_purpose_reading=interpretations['life_purpose_reading']
            )

        return render(request, 'core/natal_chart_result.html', {
            'natal_chart': natal_chart,
            'profile': profile
        })

    return render(request, 'core/natal_chart.html', {
        'profile': profile,
        'existing_chart': existing_chart
    })


@login_required
def statistics_view(request):
    """Страница статистики пользователя"""
    try:
        profile = ZodiacProfile.objects.get(user=request.user)
    except ZodiacProfile.DoesNotExist:
        return redirect('quiz')

    # Получаем статистику по всем знакам
    all_signs_stats = profile.get_all_sign_stats()

    # Статистика по заданиям
    total_tasks = Task.objects.filter(user=request.user).count()
    completed_tasks = Task.objects.filter(user=request.user, status='completed').count()
    in_progress_tasks = Task.objects.filter(user=request.user, status='in_progress').count()

    # Статистика по типам заданий
    books_completed = Task.objects.filter(
        user=request.user,
        status='completed',
        task_type='book'
    ).count()
    movies_completed = Task.objects.filter(
        user=request.user,
        status='completed',
        task_type='movie'
    ).count()
    series_completed = Task.objects.filter(
        user=request.user,
        status='completed',
        task_type='series'
    ).count()

    # Статистика по записям
    total_entries = DailyEntry.objects.filter(user=request.user).count()

    # Средний уровень эмоций
    entries_emotions = DailyEntry.objects.filter(user=request.user).values_list('emotion_level', flat=True)
    avg_emotion = sum(entries_emotions) / len(entries_emotions) if entries_emotions else 5

    # Статистика по Таро
    total_tarot = TarotReading.objects.filter(user=request.user).count()

    # Текущий знак и его прогресс
    current_sign = profile.inner_sign
    current_sign_level = profile.get_sign_level(current_sign.name) if current_sign else 1
    current_sign_exp = profile.get_sign_experience(current_sign.name) if current_sign else 0
    exp_to_next = profile.XP_PER_LEVEL
    current_sign_progress = int((current_sign_exp / exp_to_next) * 100)

    # Топ-3 знака по уровню
    top_signs = all_signs_stats[:3]

    context = {
        'profile': profile,
        'all_signs_stats': all_signs_stats,
        'current_sign': current_sign,
        'current_sign_level': current_sign_level,
        'current_sign_exp': current_sign_exp,
        'current_sign_progress': current_sign_progress,
        'exp_to_next': exp_to_next,
        'top_signs': top_signs,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'in_progress_tasks': in_progress_tasks,
        'books_completed': books_completed,
        'movies_completed': movies_completed,
        'series_completed': series_completed,
        'total_entries': total_entries,
        'avg_emotion': round(avg_emotion, 1),
        'total_tarot': total_tarot,
        'user': request.user
    }

    return render(request, 'core/statistics.html', context)
