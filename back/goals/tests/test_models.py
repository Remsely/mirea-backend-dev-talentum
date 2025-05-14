from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import User, Employee
from goals.models import Goal, Progress


class ModelTestsMixin:
    """Миксин для создания общих объектов для всех тестов моделей"""

    @classmethod
    def setUpTestData(cls):
        """Создание общих тестовых данных"""
        today = timezone.now().date()
        end_date = today + timedelta(days=30)

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
            'end_period': end_date,
        }


class GoalModelTests(ModelTestsMixin, APITestCase):
    """Тесты логики модели Goal"""

    def setUp(self):
        """Создание цели перед каждым тестом"""
        self.goal = Goal.objects.create(
            status=Goal.STATUS_DRAFT,
            **self.__class__.goal_data
        )

    def test_goal_str_representation(self):
        """Тест строкового представления цели"""
        self.assertEqual(
            str(self.goal),
            f"Test Goal - {self.__class__.employee.user.get_full_name()}"
        )

    def test_goal_status_methods(self):
        """Тест методов проверки статуса цели"""
        # В статусе Draft
        self.assertTrue(self.goal.can_be_submitted())
        self.assertFalse(self.goal.can_be_approved())
        self.assertFalse(self.goal.can_add_progress())
        self.assertFalse(self.goal.can_complete())
        self.assertFalse(self.goal.can_add_self_assessment())
        self.assertFalse(self.goal.can_request_feedback())
        self.assertFalse(self.goal.can_add_expert_evaluation())

        # В статусе Pending Approval
        self.goal.status = Goal.STATUS_PENDING_APPROVAL
        self.goal.save()
        self.assertFalse(self.goal.can_be_submitted())
        self.assertTrue(self.goal.can_be_approved())
        self.assertFalse(self.goal.can_add_progress())
        self.assertFalse(self.goal.can_complete())
        self.assertFalse(self.goal.can_add_self_assessment())
        self.assertFalse(self.goal.can_request_feedback())
        self.assertFalse(self.goal.can_add_expert_evaluation())

        # В статусе In Progress
        self.goal.status = Goal.STATUS_IN_PROGRESS
        self.goal.save()
        self.assertFalse(self.goal.can_be_submitted())
        self.assertFalse(self.goal.can_be_approved())
        self.assertTrue(self.goal.can_add_progress())
        self.assertTrue(self.goal.can_complete())
        self.assertTrue(self.goal.can_add_self_assessment())
        self.assertFalse(self.goal.can_request_feedback())
        self.assertFalse(self.goal.can_add_expert_evaluation())

        # В статусе Pending Assessment
        self.goal.status = Goal.STATUS_PENDING_ASSESSMENT
        self.goal.save()
        self.assertFalse(self.goal.can_be_submitted())
        self.assertFalse(self.goal.can_be_approved())
        self.assertFalse(self.goal.can_add_progress())
        self.assertFalse(self.goal.can_complete())
        self.assertTrue(self.goal.can_add_self_assessment())
        self.assertTrue(self.goal.can_request_feedback())
        self.assertTrue(self.goal.can_add_expert_evaluation())


class ProgressModelTests(ModelTestsMixin, APITestCase):
    """Тесты логики модели Progress"""

    def setUp(self):
        """Создание цели в статусе 'В процессе' перед каждым тестом"""
        self.goal = Goal.objects.create(
            status=Goal.STATUS_IN_PROGRESS,
            **self.__class__.goal_data
        )

    def test_progress_str_representation(self):
        """Тест строкового представления прогресса"""
        progress = Progress.objects.create(
            goal=self.goal,
            description='Test Progress'
        )

        expected_str = (f"Прогресс для {self.goal.title} "
                        f"от {progress.created_dttm.strftime('%d.%m.%Y')}")
        self.assertEqual(str(progress), expected_str)
