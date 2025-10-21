#!/usr/bin/env python
"""
Скрипт для полной очистки базы данных
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'soulmirror.settings')
django.setup()

from core.models import (
    User, DailyEntry, DailyAdvice, Task, TarotReading
)

def clear_all_data():
    """Удаляет все данные пользователей из БД"""
    print("Удаление данных...")

    # Удаляем связанные данные
    TarotReading.objects.all().delete()
    print("✓ Удалены расклады Таро")

    Task.objects.all().delete()
    print("✓ Удалены задания")

    DailyAdvice.objects.all().delete()
    print("✓ Удалены ежедневные советы")

    DailyEntry.objects.all().delete()
    print("✓ Удалены дневниковые записи")

    # Удаляем пользователей (кроме суперпользователей, если хотите их сохранить)
    User.objects.filter(is_superuser=False).delete()
    print("✓ Удалены пользователи")

    # Или удалить ВСЕХ пользователей:
    # User.objects.all().delete()
    # print("✓ Удалены ВСЕ пользователи")

    print("\n✅ База данных очищена!")

if __name__ == '__main__':
    confirm = input("Вы уверены, что хотите удалить ВСЕ данные? (yes/no): ")
    if confirm.lower() == 'yes':
        clear_all_data()
    else:
        print("Отменено")
