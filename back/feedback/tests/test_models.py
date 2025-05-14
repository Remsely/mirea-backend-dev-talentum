from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import User, Employee
from goals.models import Goal
from feedback.models import SelfAssessment


class SelfAssessmentModelTests(APITestCase):
    """Тесты логики модели SelfAssessment"""

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

        # Создаем сотрудника
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

    def setUp(self):
        """Создание цели в статусе 'В процессе' перед каждым тестом"""
        self.goal = Goal.objects.create(
            status=Goal.STATUS_IN_PROGRESS,
            **self.__class__.goal_data
        )

    def test_self_assessment_str_representation(self):
        """Тест строкового представления самооценки"""
        assessment = SelfAssessment.objects.create(
            goal=self.goal,
            rating=8,
            comments='Test Comments',
            areas_to_improve='Test Areas'
        )
        self.assertEqual(str(assessment), f"Самооценка для {self.goal.title}") 