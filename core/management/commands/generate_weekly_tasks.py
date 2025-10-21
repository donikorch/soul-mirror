"""
Management команда для генерации еженедельных заданий
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import User, ZodiacSign, Task, ZodiacProfile
from core.ai.agent import SoulMirrorAgent
from django.conf import settings
import random


class Command(BaseCommand):
    help = 'Генерирует еженедельные задания для всех пользователей'

    def handle(self, *args, **options):
        self.stdout.write('Генерация еженедельных заданий...')

        ai_agent = SoulMirrorAgent(
            ollama_url=settings.OLLAMA_API_URL,
            model=settings.OLLAMA_MODEL
        )

        # Получаем всех активных пользователей
        users = User.objects.filter(completed_initial_quiz=True)

        for user in users:
            try:
                # Проверяем, есть ли уже задания на эту неделю
                week_ago = timezone.now() - timedelta(days=7)
                recent_tasks = Task.objects.filter(
                    user=user,
                    assigned_at__gte=week_ago
                ).count()

                if recent_tasks >= 3:
                    self.stdout.write(f'  У {user.username} уже есть задания на эту неделю')
                    continue

                # Получаем профиль пользователя
                try:
                    profile = ZodiacProfile.objects.get(user=user)
                except ZodiacProfile.DoesNotExist:
                    continue

                # Выбираем целевой знак для развития
                # Можно выбрать случайный или тот, к которому меньше всего прогресса
                all_signs = ZodiacSign.objects.all()

                if profile.sign_progress:
                    # Выбираем знак с наименьшим прогрессом
                    min_sign_name = min(profile.sign_progress.items(), key=lambda x: x[1])[0]
                    target_sign = ZodiacSign.objects.get(name=min_sign_name)
                else:
                    # Случайный знак
                    target_sign = random.choice(all_signs)

                # Генерируем рекомендацию
                user_profile_data = {
                    'inner_sign': profile.inner_sign.get_name_display() if profile.inner_sign else 'Овен',
                    'level': user.level,
                    'experience': user.total_experience
                }

                # Получаем список всех уже существующих заданий пользователя
                existing_titles = set(Task.objects.filter(user=user).values_list('title', flat=True))

                # Пытаемся сгенерировать уникальное задание (максимум 5 попыток)
                max_attempts = 5
                task = None
                for attempt in range(max_attempts):
                    recommendation = ai_agent.generate_task_recommendation(
                        user_profile_data,
                        target_sign.get_name_display(),
                        existing_titles
                    )

                    # Проверяем, что такого задания еще нет
                    if recommendation['title'] not in existing_titles:
                        # Создаем задание
                        task = Task.objects.create(
                            user=user,
                            task_type=recommendation['task_type'],
                            title=recommendation['title'],
                            author=recommendation.get('author'),
                            description=recommendation['description'],
                            target_sign=target_sign,
                            experience_reward=random.randint(80, 150),
                            status='assigned'
                        )
                        break
                    elif attempt == max_attempts - 1:
                        # Последняя попытка - создаем в любом случае
                        self.stdout.write(
                            self.style.WARNING(f'  ⚠ Не удалось создать уникальное задание за {max_attempts} попыток для {user.username}')
                        )
                        task = Task.objects.create(
                            user=user,
                            task_type=recommendation['task_type'],
                            title=recommendation['title'],
                            author=recommendation.get('author'),
                            description=recommendation['description'],
                            target_sign=target_sign,
                            experience_reward=random.randint(80, 150),
                            status='assigned'
                        )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✓ Создано задание для {user.username}: {task.title}'
                    )
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Ошибка для {user.username}: {str(e)}')
                )

        self.stdout.write(self.style.SUCCESS('Генерация заданий завершена!'))
