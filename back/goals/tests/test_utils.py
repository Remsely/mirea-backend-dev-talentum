from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User, Employee
from goals.models import Goal


class UtilityMethodsTestCase(APITestCase):
    """Тесты вспомогательных методов и утилит"""

    @classmethod
    def setUpTestData(cls):
        """Создание данных для всех тестов"""
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

        # Базовые данные для тестовой цели
        cls.goal_data = {
            'employee': cls.employee,
            'title': 'Test Goal',
            'description': 'Test Description',
            'expected_results': 'Test Expected Results',
            'start_period': today,
            'end_period': today + timedelta(days=30),
        }

    def test_goal_status_transitions(self):
        """Тест переходов между статусами цели"""
        goal = Goal.objects.create(
            status=Goal.STATUS_DRAFT,
            **self.__class__.goal_data
        )

        # Проверка методов возможных переходов
        self.assertTrue(goal.can_be_submitted())
        self.assertFalse(goal.can_be_approved())
        self.assertFalse(goal.can_add_progress())
        self.assertFalse(goal.can_complete())

        # Переход к статусу "На согласовании"
        goal.status = Goal.STATUS_PENDING_APPROVAL
        goal.save()

        self.assertFalse(goal.can_be_submitted())
        self.assertTrue(goal.can_be_approved())
        self.assertFalse(goal.can_add_progress())
        self.assertFalse(goal.can_complete())

        # Переход к статусу "В процессе"
        goal.status = Goal.STATUS_IN_PROGRESS
        goal.save()

        self.assertFalse(goal.can_be_submitted())
        self.assertFalse(goal.can_be_approved())
        self.assertTrue(goal.can_add_progress())
        self.assertTrue(goal.can_complete())

        # Переход к статусу "Ожидает оценки"
        goal.status = Goal.STATUS_PENDING_ASSESSMENT
        goal.save()

        self.assertFalse(goal.can_be_submitted())
        self.assertFalse(goal.can_be_approved())
        self.assertFalse(goal.can_add_progress())
        self.assertFalse(goal.can_complete())
        self.assertTrue(goal.can_add_self_assessment())

    def test_invalid_date_validation(self):
        """Тест валидации некорректных дат периода"""
        # Проверка валидации через API
        self.client.force_authenticate(user=self.__class__.employee_user)

        today = timezone.now().date()
        data = {
            'title': 'Invalid Date Goal',
            'description': 'Invalid Date Description',
            'expected_results': 'Invalid Date Expected Results',
            'start_period': (today + timedelta(days=10)).isoformat(),
            'end_period': today.isoformat(),  # Конец раньше начала
        }

        response = self.client.post(reverse('goal-list'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('end_period', response.data)
