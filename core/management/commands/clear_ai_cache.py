"""
Django management команда для очистки старых AI данных из БД
"""
from django.core.management.base import BaseCommand
from core.models import DailyAdvice, TarotReading, NatalChart


class Command(BaseCommand):
    help = 'Очищает старые AI данные из базы данных для регенерации'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Удалить все данные (советы, таро, натальные карты)',
        )
        parser.add_argument(
            '--advice',
            action='store_true',
            help='Удалить только советы дня',
        )
        parser.add_argument(
            '--tarot',
            action='store_true',
            help='Удалить только расклады таро',
        )
        parser.add_argument(
            '--natal',
            action='store_true',
            help='Удалить только натальные карты',
        )

    def handle(self, *args, **options):
        if options['all']:
            # Удаляем все
            advice_count = DailyAdvice.objects.all().count()
            tarot_count = TarotReading.objects.all().count()
            natal_count = NatalChart.objects.all().count()

            DailyAdvice.objects.all().delete()
            TarotReading.objects.all().delete()
            NatalChart.objects.all().delete()

            self.stdout.write(
                self.style.SUCCESS(
                    f'Успешно удалено:\n'
                    f'- Советов дня: {advice_count}\n'
                    f'- Раскладов таро: {tarot_count}\n'
                    f'- Натальных карт: {natal_count}'
                )
            )
        elif options['advice']:
            count = DailyAdvice.objects.all().count()
            DailyAdvice.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS(f'Удалено советов дня: {count}')
            )
        elif options['tarot']:
            count = TarotReading.objects.all().count()
            TarotReading.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS(f'Удалено раскладов таро: {count}')
            )
        elif options['natal']:
            count = NatalChart.objects.all().count()
            NatalChart.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS(f'Удалено натальных карт: {count}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    'Не выбрана опция. Используйте --all, --advice, --tarot или --natal'
                )
            )
