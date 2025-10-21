"""
Management команда для инициализации базовых данных
"""
from django.core.management.base import BaseCommand
from core.models import ZodiacSign, QuizQuestion, QuizAnswer


class Command(BaseCommand):
    help = 'Инициализирует базовые данные: знаки зодиака и опросник'

    def handle(self, *args, **options):
        self.stdout.write('Начинаем инициализацию данных...')

        # Создаем знаки зодиака
        self.create_zodiac_signs()

        # Создаем вопросы опросника
        self.create_quiz_questions()

        self.stdout.write(self.style.SUCCESS('Данные успешно инициализированы!'))

    def create_zodiac_signs(self):
        self.stdout.write('Создание знаков зодиака...')

        zodiac_data = [
            ('aries', 'Овен', ['энергичность', 'лидерство', 'решительность', 'импульсивность']),
            ('taurus', 'Телец', ['упорство', 'надежность', 'практичность', 'терпение']),
            ('gemini', 'Близнецы', ['общительность', 'любознательность', 'адаптивность', 'многогранность']),
            ('cancer', 'Рак', ['эмоциональность', 'заботливость', 'интуитивность', 'защитность']),
            ('leo', 'Лев', ['уверенность', 'творчество', 'великодушие', 'амбициозность']),
            ('virgo', 'Дева', ['аналитичность', 'перфекционизм', 'практичность', 'служение']),
            ('libra', 'Весы', ['гармония', 'справедливость', 'дипломатичность', 'эстетизм']),
            ('scorpio', 'Скорпион', ['интенсивность', 'трансформация', 'глубина', 'страсть']),
            ('sagittarius', 'Стрелец', ['оптимизм', 'философичность', 'свобода', 'авантюризм']),
            ('capricorn', 'Козерог', ['амбициозность', 'дисциплина', 'ответственность', 'прагматизм']),
            ('aquarius', 'Водолей', ['инновационность', 'независимость', 'гуманизм', 'оригинальность']),
            ('pisces', 'Рыбы', ['интуиция', 'сострадание', 'творчество', 'мистичность']),
        ]

        for name, display_name, traits in zodiac_data:
            sign, created = ZodiacSign.objects.get_or_create(
                name=name,
                defaults={
                    'description': f'{display_name} - один из 12 знаков зодиака',
                    'traits': traits
                }
            )
            if created:
                self.stdout.write(f'  Создан знак: {display_name}')

    def create_quiz_questions(self):
        self.stdout.write('Создание вопросов опросника...')

        # Вопрос 1
        q1, created = QuizQuestion.objects.get_or_create(
            order=1,
            defaults={'question_text': 'Как вы обычно принимаете важные решения?'}
        )

        if created:
            QuizAnswer.objects.create(
                question=q1,
                answer_text='Быстро и импульсивно, доверяясь интуиции',
                sign_weights={'aries': 3, 'sagittarius': 2, 'leo': 1}
            )
            QuizAnswer.objects.create(
                question=q1,
                answer_text='Тщательно взвешиваю все за и против',
                sign_weights={'virgo': 3, 'capricorn': 2, 'libra': 2}
            )
            QuizAnswer.objects.create(
                question=q1,
                answer_text='Прислушиваюсь к своим эмоциям и чувствам',
                sign_weights={'pisces': 3, 'cancer': 2, 'scorpio': 1}
            )
            QuizAnswer.objects.create(
                question=q1,
                answer_text='Ищу инновационные и нестандартные решения',
                sign_weights={'aquarius': 3, 'gemini': 2}
            )

        # Вопрос 2
        q2, created = QuizQuestion.objects.get_or_create(
            order=2,
            defaults={'question_text': 'Что для вас является главным источником энергии?'}
        )

        if created:
            QuizAnswer.objects.create(
                question=q2,
                answer_text='Общение с людьми и новые знакомства',
                sign_weights={'gemini': 3, 'libra': 2, 'leo': 2}
            )
            QuizAnswer.objects.create(
                question=q2,
                answer_text='Достижение целей и успех',
                sign_weights={'capricorn': 3, 'aries': 2, 'leo': 2}
            )
            QuizAnswer.objects.create(
                question=q2,
                answer_text='Забота о близких и уют дома',
                sign_weights={'cancer': 3, 'taurus': 2, 'virgo': 1}
            )
            QuizAnswer.objects.create(
                question=q2,
                answer_text='Познание мира и новые впечатления',
                sign_weights={'sagittarius': 3, 'aquarius': 2, 'pisces': 1}
            )

        # Вопрос 3
        q3, created = QuizQuestion.objects.get_or_create(
            order=3,
            defaults={'question_text': 'Как вы реагируете на конфликтные ситуации?'}
        )

        if created:
            QuizAnswer.objects.create(
                question=q3,
                answer_text='Сразу вступаю в борьбу, отстаиваю свою позицию',
                sign_weights={'aries': 3, 'scorpio': 2, 'leo': 2}
            )
            QuizAnswer.objects.create(
                question=q3,
                answer_text='Стараюсь найти компромисс и восстановить гармонию',
                sign_weights={'libra': 3, 'pisces': 2, 'cancer': 1}
            )
            QuizAnswer.objects.create(
                question=q3,
                answer_text='Анализирую ситуацию и ищу рациональное решение',
                sign_weights={'virgo': 3, 'capricorn': 2, 'aquarius': 1}
            )
            QuizAnswer.objects.create(
                question=q3,
                answer_text='Предпочитаю избегать конфликтов или переждать',
                sign_weights={'taurus': 2, 'cancer': 2, 'pisces': 2}
            )

        # Вопрос 4
        q4, created = QuizQuestion.objects.get_or_create(
            order=4,
            defaults={'question_text': 'Что вас больше всего мотивирует в жизни?'}
        )

        if created:
            QuizAnswer.objects.create(
                question=q4,
                answer_text='Признание, внимание и восхищение окружающих',
                sign_weights={'leo': 3, 'aries': 2, 'libra': 1}
            )
            QuizAnswer.objects.create(
                question=q4,
                answer_text='Стабильность, безопасность и материальное благополучие',
                sign_weights={'taurus': 3, 'capricorn': 2, 'virgo': 2}
            )
            QuizAnswer.objects.create(
                question=q4,
                answer_text='Глубокие эмоциональные связи и трансформация',
                sign_weights={'scorpio': 3, 'pisces': 2, 'cancer': 2}
            )
            QuizAnswer.objects.create(
                question=q4,
                answer_text='Свобода, исследования и расширение границ',
                sign_weights={'sagittarius': 3, 'aquarius': 2, 'gemini': 2}
            )

        # Вопрос 5
        q5, created = QuizQuestion.objects.get_or_create(
            order=5,
            defaults={'question_text': 'Какой стиль работы вам ближе?'}
        )

        if created:
            QuizAnswer.objects.create(
                question=q5,
                answer_text='Быстро, с энтузиазмом, беру инициативу в свои руки',
                sign_weights={'aries': 3, 'leo': 2, 'sagittarius': 1}
            )
            QuizAnswer.objects.create(
                question=q5,
                answer_text='Методично, тщательно, внимание к деталям',
                sign_weights={'virgo': 3, 'capricorn': 2, 'taurus': 2}
            )
            QuizAnswer.objects.create(
                question=q5,
                answer_text='Творчески, с вдохновением, нестандартно',
                sign_weights={'pisces': 3, 'aquarius': 2, 'gemini': 2}
            )
            QuizAnswer.objects.create(
                question=q5,
                answer_text='В команде, сотрудничая и помогая другим',
                sign_weights={'libra': 3, 'cancer': 2, 'pisces': 1}
            )

        self.stdout.write(self.style.SUCCESS('Опросник создан!'))
