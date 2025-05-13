from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import User, Employee
from goals.models import Goal, Progress, SelfAssessment


class SerializersTestMixin:
    """Миксин для создания общих объектов для тестов сериализаторов"""

    @classmethod
    def setUpTestData(cls):
        """Создание общих тестовых данных"""
        today = timezone.now().date()

        # Создаем менеджера
        cls.manager_user = User.objects.create_user(
            username='manager',
            password='password123',
            email='manager@example.com',
            first_name='Manager',
            last_name='User',
            role='manager'
        )
        cls.manager = Employee.objects.create(
            user=cls.manager_user,
            position='Team Lead',
            hire_dt=today
        )

        # Создаем обычного сотрудника
        cls.employee_user = User.objects.create_user(
            username='employee',
            password='password123',
            email='employee@example.com',
            first_name='Employee',
            last_name='User',
            role='employee'
        )
        cls.employee = Employee.objects.create(
            user=cls.employee_user,
            position='Developer',
            hire_dt=today,
            manager=cls.manager
        )

        # Общие данные для целей
        cls.goal_data = {
            'employee': cls.employee,
            'title': 'Test Goal',
            'description': 'Test Description',
            'expected_results': 'Test Expected Results',
            'start_period': today,
            'end_period': today + timedelta(days=30),
        }


class GoalSerializersTestCase(SerializersTestMixin, APITestCase):
    """Тесты сериализаторов для модуля целей"""

    def setUp(self):
        """Создание тестовых объектов перед каждым тестом"""
        # Создаем тестовую цель
        self.goal = Goal.objects.create(
            status=Goal.STATUS_IN_PROGRESS,
            **self.__class__.goal_data
        )

        # Создаем запись о прогрессе
        self.progress = Progress.objects.create(
            goal=self.goal,
            description='Test Progress'
        )

        # Создаем запись о самооценке
        self.assessment = SelfAssessment.objects.create(
            goal=self.goal,
            rating=8,
            comments='Test Assessment',
            areas_to_improve='Test Areas'
        )

    def test_goal_detail_serializer(self):
        """Тест сериализатора GoalDetailSerializer"""
        from goals.serializers import GoalDetailSerializer

        serializer = GoalDetailSerializer(self.goal)
        data = serializer.data

        # Проверяем основные поля
        self.assertEqual(data['title'], 'Test Goal')
        self.assertEqual(data['description'], 'Test Description')
        self.assertEqual(data['expected_results'], 'Test Expected Results')
        self.assertEqual(data['status'], Goal.STATUS_IN_PROGRESS)

        # Проверяем связанные объекты
        self.assertEqual(len(data['progress_updates']), 1)
        self.assertEqual(
            data['progress_updates'][0]['description'],
            'Test Progress'
        )

        self.assertIsNotNone(data['self_assessment'])
        self.assertEqual(data['self_assessment']['rating'], 8)
        self.assertEqual(data['self_assessment']['comments'],
                         'Test Assessment')
        self.assertEqual(data['self_assessment']['areas_to_improve'],
                         'Test Areas')

        # Проверяем вычисляемые поля
        self.assertEqual(data['can_be_submitted'], False)
        self.assertEqual(data['can_be_approved'], False)
        self.assertEqual(data['can_add_progress'], True)
        self.assertEqual(data['can_add_self_assessment'], True)
        self.assertEqual(data['can_complete'], True)

    def test_goal_list_serializer(self):
        """Тест сериализатора GoalListSerializer"""
        from goals.serializers import GoalListSerializer

        serializer = GoalListSerializer(self.goal)
        data = serializer.data

        # Проверяем, что в списочном представлении меньше полей
        self.assertEqual(data['title'], 'Test Goal')
        self.assertEqual(data['status'], Goal.STATUS_IN_PROGRESS)
        self.assertIn('employee', data)
        self.assertNotIn('description', data)
        self.assertNotIn('expected_results', data)
        self.assertNotIn('progress_updates', data)
        self.assertNotIn('self_assessment', data)

    def test_progress_serializer(self):
        """Тест сериализатора ProgressSerializer"""
        from goals.serializers import ProgressSerializer

        serializer = ProgressSerializer(self.progress)
        data = serializer.data

        self.assertEqual(data['description'], 'Test Progress')
        self.assertIn('created_dttm', data)

    def test_self_assessment_serializer(self):
        """Тест сериализатора SelfAssessmentSerializer"""
        from goals.serializers import SelfAssessmentSerializer

        serializer = SelfAssessmentSerializer(self.assessment)
        data = serializer.data

        self.assertEqual(data['rating'], 8)
        self.assertEqual(data['comments'], 'Test Assessment')
        self.assertEqual(data['areas_to_improve'], 'Test Areas')
        self.assertIn('created_dttm', data)

    def test_goal_create_serializer_validation(self):
        """Тест валидации в GoalCreateSerializer"""
        from goals.serializers import GoalCreateSerializer

        # Тест с некорректными датами (дата окончания раньше начала)
        today = timezone.now().date()
        invalid_data = {
            'title': 'New Goal',
            'description': 'New Description',
            'expected_results': 'New Expected Results',
            'start_period': today,
            'end_period': today - timedelta(days=1)
        }

        context = {
            'request': type('Request', (), {'user': self.employee_user})}
        serializer = GoalCreateSerializer(data=invalid_data, context=context)

        self.assertFalse(serializer.is_valid())
        self.assertIn('end_period', serializer.errors)

        # Тест с корректными данными
        valid_data = {
            'title': 'New Goal',
            'description': 'New Description',
            'expected_results': 'New Expected Results',
            'start_period': today,
            'end_period': today + timedelta(days=30)
        }

        serializer = GoalCreateSerializer(data=valid_data, context=context)
        self.assertTrue(serializer.is_valid())
