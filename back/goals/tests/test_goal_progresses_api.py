from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User, Employee
from goals.models import Goal, Progress


class ProgressAPITestCase(APITestCase):
    """Тесты API для работы с записями о прогрессе"""

    @classmethod
    def setUpTestData(cls):
        """Создание данных для всех тестов"""
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

        # Создаем другого сотрудника
        cls.employee2_user = User.objects.create_user(
            username='employee2',
            password='password123',
            email='employee2@example.com',
            first_name='Employee2',
            last_name='User',
            role='employee'
        )
        cls.employee2 = Employee.objects.create(
            user=cls.employee2_user,
            position='Designer',
            hire_dt=today,
            manager=cls.manager
        )

        # Создаем цели и прогресс
        cls.goal_data = {
            'title': 'Test Goal',
            'description': 'Test Description',
            'expected_results': 'Test Expected Results',
            'start_period': today,
            'end_period': end_date,
        }

        cls.draft_goal_data = {
            'title': 'Draft Goal',
            'description': 'Draft Description',
            'expected_results': 'Draft Expected Results',
            'start_period': today,
            'end_period': end_date,
            'status': Goal.STATUS_DRAFT
        }

    def setUp(self):
        """Подготовка данных перед каждым тестом"""
        # Создаем цель в статусе "В процессе"
        self.goal = Goal.objects.create(
            employee=self.__class__.employee,
            status=Goal.STATUS_IN_PROGRESS,
            **self.__class__.goal_data
        )

        # Создаем цель в статусе "Черновик"
        self.draft_goal = Goal.objects.create(
            employee=self.__class__.employee,
            **self.__class__.draft_goal_data
        )

        # Создаем запись о прогрессе
        self.progress = Progress.objects.create(
            goal=self.goal,
            description='Initial Progress'
        )

        # URL-адреса для тестов
        self.progress_url = reverse('goal-progress-list',
                                    kwargs={'goal_pk': self.goal.pk})
        self.draft_goal_progress_url = reverse('goal-progress-list',
                                               kwargs={
                                                   'goal_pk': self.draft_goal.pk})

    def test_progress_list_success(self):
        """Тест получения списка записей о прогрессе"""
        self.client.force_authenticate(user=self.__class__.employee_user)

        response = self.client.get(self.progress_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['description'], 'Initial Progress')

    def test_progress_list_manager_access(self):
        """Тест доступа руководителя к записям о прогрессе подчиненного"""
        self.client.force_authenticate(user=self.__class__.manager_user)

        response = self.client.get(self.progress_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_progress_list_other_user_forbidden(self):
        """Тест доступа другого сотрудника к записям о прогрессе (должно быть запрещено)"""
        self.client.force_authenticate(user=self.__class__.employee2_user)

        response = self.client.get(self.progress_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_progress_create_success(self):
        """Тест успешного создания записи о прогрессе"""
        self.client.force_authenticate(user=self.__class__.employee_user)

        data = {
            'description': 'New Progress Update'
        }

        response = self.client.post(self.progress_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Проверяем, что запись создана
        self.assertEqual(Progress.objects.count(), 2)
        self.assertEqual(
            Progress.objects.filter(
                description='New Progress Update').count(),
            1
        )

    def test_progress_create_by_manager(self):
        """Тест создания записи о прогрессе руководителем"""
        self.client.force_authenticate(user=self.__class__.manager_user)

        data = {
            'description': 'Manager Progress Update'
        }

        response = self.client.post(self.progress_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Проверяем, что запись создана
        progress = Progress.objects.get(description='Manager Progress Update')
        self.assertEqual(progress.goal, self.goal)

    def test_progress_create_for_draft_goal_error(self):
        """Тест создания записи о прогрессе для цели в статусе черновика (должно быть ошибкой)"""
        self.client.force_authenticate(user=self.__class__.employee_user)

        data = {
            'description': 'Progress for Draft Goal'
        }

        response = self.client.post(self.draft_goal_progress_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Проверяем, что запись не создана
        self.assertFalse(
            Progress.objects.filter(
                description='Progress for Draft Goal').exists()
        )

    def test_progress_create_by_other_employee_forbidden(self):
        """Тест создания записи о прогрессе другим сотрудником (должно быть запрещено)"""
        self.client.force_authenticate(user=self.__class__.employee2_user)

        data = {
            'description': 'Other Employee Progress Update'
        }

        response = self.client.post(self.progress_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Проверяем, что запись не создана
        self.assertFalse(
            Progress.objects.filter(
                description='Other Employee Progress Update'
            ).exists()
        )
