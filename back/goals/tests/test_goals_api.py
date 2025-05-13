from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User, Employee
from goals.models import Goal


class GoalAPITestCase(APITestCase):
    """Тесты API для работы с целями"""

    @classmethod
    def setUpTestData(cls):
        """Создание данных для всех тестов"""
        today = timezone.now().date()
        end_date = today + timedelta(days=30)

        # Создаем администратора
        cls.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            role='admin',
            is_staff=True
        )

        # Создаем лидера профессии
        cls.expertise_leader_user = User.objects.create_user(
            username='expertise_leader',
            password='password123',
            email='leader@example.com',
            first_name='Expertise',
            last_name='Leader',
            role='expertise_leader'
        )
        cls.expertise_leader = Employee.objects.create(
            user=cls.expertise_leader_user,
            position='Tech Lead',
            hire_dt=today
        )

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

        # Создаем другого сотрудника без отношения к первому
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

        # Создаем пользователя без профиля сотрудника
        cls.user_without_profile = User.objects.create_user(
            username='regular',
            password='password123',
            email='regular@example.com',
            first_name='Regular',
            last_name='User',
            role='employee'
        )

        # Общие данные для целей
        cls.goal_data = {
            'title': 'Test Goal',
            'description': 'Test Description',
            'expected_results': 'Test Expected Results',
            'start_period': today,
            'end_period': end_date,
        }

        cls.goal2_data = {
            'title': 'Test Goal 2',
            'description': 'Test Description 2',
            'expected_results': 'Test Expected Results 2',
            'start_period': today,
            'end_period': end_date,
        }

        # URL базовые
        cls.goals_url = reverse('goal-list')

    def setUp(self):
        """Подготовка данных перед каждым тестом"""
        # Создаем тестовую цель
        self.goal = Goal.objects.create(
            employee=self.__class__.employee,
            status=Goal.STATUS_DRAFT,
            **self.__class__.goal_data
        )

        # Создаем цель для другого сотрудника
        self.goal2 = Goal.objects.create(
            employee=self.__class__.employee2,
            status=Goal.STATUS_DRAFT,
            **self.__class__.goal2_data
        )

        # URL-адреса для тестов с конкретными целями
        self.goal_detail_url = reverse('goal-detail',
                                       kwargs={'pk': self.goal.pk})
        self.goal2_detail_url = reverse('goal-detail',
                                        kwargs={'pk': self.goal2.pk})
        self.goal_submit_url = reverse('goal-submit',
                                       kwargs={'pk': self.goal.pk})
        self.goal_approve_url = reverse('goal-approve',
                                        kwargs={'pk': self.goal.pk})
        self.goal_complete_url = reverse('goal-complete',
                                         kwargs={'pk': self.goal.pk})
        self.progress_url = reverse('goal-progress-list',
                                    kwargs={'goal_pk': self.goal.pk})
        self.self_assessment_url = reverse('goal-self-assessment-list',
                                           kwargs={'goal_pk': self.goal.pk})
        self.self_assessment_detail_url = reverse(
            'goal-self-assessment-detail',
            kwargs={'goal_pk': self.goal.pk, 'pk': 1})

    def test_goal_list_employee_own_goals(self):
        """Тест получения списка целей (сотрудник видит только свои цели)"""
        self.client.force_authenticate(user=self.__class__.employee_user)

        response = self.client.get(self.__class__.goals_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Сотрудник должен видеть только свои цели
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.goal.id)

    def test_goal_list_manager_all_team_goals(self):
        """Тест получения списка целей (руководитель видит цели команды)"""
        self.client.force_authenticate(user=self.__class__.manager_user)

        response = self.client.get(self.__class__.goals_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Руководитель должен видеть цели всех подчиненных
        self.assertEqual(len(response.data), 2)
        goal_ids = [goal['id'] for goal in response.data]
        self.assertIn(self.goal.id, goal_ids)
        self.assertIn(self.goal2.id, goal_ids)

    def test_goal_list_admin_all_goals(self):
        """Тест получения списка целей (администратор видит все цели)"""
        self.client.force_authenticate(user=self.__class__.admin_user)

        response = self.client.get(self.__class__.goals_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Администратор должен видеть все цели
        self.assertEqual(len(response.data), 2)

    def test_goal_list_expertise_leader_own_goals_and_pending_assessment(self):
        """Тест получения списка целей (лидер профессии видит свои цели и ожидающие оценки)"""
        # Создаем цель для лидера профессии
        Goal.objects.create(
            employee=self.__class__.expertise_leader,
            title='Leader Goal',
            description='Leader Description',
            expected_results='Leader Expected Results',
            start_period=timezone.now().date(),
            end_period=timezone.now().date() + timedelta(days=30),
            status=Goal.STATUS_DRAFT
        )

        # Переводим одну из целей в статус "Ожидает оценки"
        self.goal2.status = Goal.STATUS_PENDING_ASSESSMENT
        self.goal2.save()

        self.client.force_authenticate(
            user=self.__class__.expertise_leader_user)

        response = self.client.get(self.__class__.goals_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Лидер профессии должен видеть свои цели и цели в статусе "Ожидает оценки"
        self.assertEqual(len(response.data), 2)  # 1 своя + 1 ожидающая оценки

    def test_goal_detail_employee_own_goal(self):
        """Тест получения детальной информации о цели (сотрудник - своя цель)"""
        self.client.force_authenticate(user=self.__class__.employee_user)

        response = self.client.get(self.goal_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.goal.id)
        self.assertEqual(response.data['title'], self.goal.title)

    def test_goal_detail_employee_other_goal_forbidden(self):
        """Тест получения детальной информации о цели (сотрудник - чужая цель)"""
        self.client.force_authenticate(user=self.__class__.employee_user)

        response = self.client.get(self.goal2_detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_goal_detail_manager_team_goals(self):
        """Тест получения детальной информации о цели (руководитель - цель подчиненного)"""
        self.client.force_authenticate(user=self.__class__.manager_user)

        response = self.client.get(self.goal_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.goal.id)

    def test_goal_create_success(self):
        """Тест успешного создания новой цели"""
        self.client.force_authenticate(user=self.__class__.employee_user)

        today = timezone.now().date()
        data = {
            'title': 'New Goal',
            'description': 'New Description',
            'expected_results': 'New Expected Results',
            'start_period': today.isoformat(),
            'end_period': (today + timedelta(days=30)).isoformat(),
        }

        response = self.client.post(self.__class__.goals_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Проверяем общее количество целей
        self.assertEqual(Goal.objects.count(), 3)

        # Проверяем, что новая цель создана с правильными данными
        new_goal = Goal.objects.get(title='New Goal')
        self.assertEqual(new_goal.employee, self.__class__.employee)
        self.assertEqual(new_goal.status, Goal.STATUS_DRAFT)
        self.assertEqual(new_goal.description, 'New Description')

    def test_goal_create_invalid_dates(self):
        """Тест создания цели с невалидными датами"""
        self.client.force_authenticate(user=self.__class__.employee_user)

        today = timezone.now().date()
        data = {
            'title': 'New Goal',
            'description': 'New Description',
            'expected_results': 'New Expected Results',
            'start_period': today.isoformat(),
            'end_period': today.isoformat(),  # Та же дата что и начало
        }

        response = self.client.post(self.__class__.goals_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('end_period', response.data)

    def test_goal_create_without_employee_profile(self):
        """Тест создания цели пользователем без профиля сотрудника"""
        self.client.force_authenticate(
            user=self.__class__.user_without_profile)

        today = timezone.now().date()
        data = {
            'title': 'New Goal',
            'description': 'New Description',
            'expected_results': 'New Expected Results',
            'start_period': today.isoformat(),
            'end_period': (today + timedelta(days=30)).isoformat(),
        }

        response = self.client.post(self.__class__.goals_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_goal_update_success(self):
        """Тест успешного обновления цели в статусе черновика"""
        self.client.force_authenticate(user=self.__class__.employee_user)

        today = timezone.now().date()
        data = {
            'title': 'Updated Goal',
            'description': 'Updated Description',
            'expected_results': 'Updated Expected Results',
            'start_period': today.isoformat(),
            'end_period': (today + timedelta(days=60)).isoformat(),
        }

        response = self.client.put(self.goal_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что цель обновлена
        self.goal.refresh_from_db()
        self.assertEqual(self.goal.title, 'Updated Goal')
        self.assertEqual(self.goal.description, 'Updated Description')

    def test_goal_update_non_draft_forbidden(self):
        """Тест обновления цели не в статусе черновика (должно быть запрещено)"""
        # Меняем статус цели
        self.goal.status = Goal.STATUS_PENDING_APPROVAL
        self.goal.save()

        self.client.force_authenticate(user=self.__class__.employee_user)

        today = timezone.now().date()
        data = {
            'title': 'Updated Goal',
            'description': 'Updated Description',
            'expected_results': 'Updated Expected Results',
            'start_period': today.isoformat(),
            'end_period': (today + timedelta(days=60)).isoformat(),
        }

        response = self.client.put(self.goal_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_goal_delete_draft_success(self):
        """Тест успешного удаления цели в статусе черновика"""
        self.client.force_authenticate(user=self.__class__.employee_user)

        response = self.client.delete(self.goal_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Проверяем, что цель удалена
        with self.assertRaises(Goal.DoesNotExist):
            Goal.objects.get(pk=self.goal.pk)

    def test_goal_delete_non_draft_forbidden(self):
        """Тест удаления цели не в статусе черновика (должно быть запрещено)"""
        # Меняем статус цели
        self.goal.status = Goal.STATUS_PENDING_APPROVAL
        self.goal.save()

        self.client.force_authenticate(user=self.__class__.employee_user)

        response = self.client.delete(self.goal_detail_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Проверяем, что цель не удалена
        self.assertTrue(Goal.objects.filter(pk=self.goal.pk).exists())

    def test_goal_submit_success(self):
        """Тест успешной отправки цели на согласование"""
        self.client.force_authenticate(user=self.__class__.employee_user)

        response = self.client.post(self.goal_submit_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что статус цели изменился
        self.goal.refresh_from_db()
        self.assertEqual(self.goal.status, Goal.STATUS_PENDING_APPROVAL)

    def test_goal_submit_already_submitted(self):
        """Тест отправки на согласование цели, которая уже не в статусе черновика"""
        # Меняем статус цели
        self.goal.status = Goal.STATUS_PENDING_APPROVAL
        self.goal.save()

        self.client.force_authenticate(user=self.__class__.employee_user)

        response = self.client.post(self.goal_submit_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_goal_submit_without_manager(self):
        """Тест отправки на согласование без руководителя"""
        # Удаляем руководителя у сотрудника
        self.__class__.employee.manager = None
        self.__class__.employee.save()

        self.client.force_authenticate(user=self.__class__.employee_user)

        response = self.client.post(self.goal_submit_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)

        # Восстанавливаем руководителя для других тестов
        self.__class__.employee.manager = self.__class__.manager
        self.__class__.employee.save()

    def test_goal_approve_by_manager_success(self):
        """Тест успешного согласования цели руководителем"""
        # Меняем статус цели на "На согласовании"
        self.goal.status = Goal.STATUS_PENDING_APPROVAL
        self.goal.save()

        self.client.force_authenticate(user=self.__class__.manager_user)

        response = self.client.post(self.goal_approve_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что статус цели изменился
        self.goal.refresh_from_db()
        self.assertEqual(self.goal.status, Goal.STATUS_IN_PROGRESS)

    def test_goal_approve_not_by_manager_forbidden(self):
        """Тест согласования цели не руководителем (должно быть запрещено)"""
        # Меняем статус цели на "На согласовании"
        self.goal.status = Goal.STATUS_PENDING_APPROVAL
        self.goal.save()

        self.client.force_authenticate(user=self.__class__.employee2_user)

        response = self.client.post(self.goal_approve_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Проверяем, что статус цели не изменился
        self.goal.refresh_from_db()
        self.assertEqual(self.goal.status, Goal.STATUS_PENDING_APPROVAL)

    def test_goal_approve_not_pending_approval(self):
        """Тест согласования цели не в статусе "На согласовании" (должно быть ошибкой)"""
        self.client.force_authenticate(user=self.__class__.manager_user)

        response = self.client.post(self.goal_approve_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Проверяем, что статус цели не изменился
        self.goal.refresh_from_db()
        self.assertEqual(self.goal.status, Goal.STATUS_DRAFT)

    def test_goal_complete_success(self):
        """Тест успешного завершения цели"""
        # Меняем статус цели на "В процессе"
        self.goal.status = Goal.STATUS_IN_PROGRESS
        self.goal.save()

        self.client.force_authenticate(user=self.__class__.employee_user)

        response = self.client.post(self.goal_complete_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что статус цели изменился
        self.goal.refresh_from_db()
        self.assertEqual(self.goal.status, Goal.STATUS_PENDING_ASSESSMENT)

    def test_goal_complete_not_in_progress(self):
        """Тест завершения цели не в статусе "В процессе" (должно быть ошибкой)"""
        self.client.force_authenticate(user=self.__class__.employee_user)

        response = self.client.post(self.goal_complete_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Проверяем, что статус цели не изменился
        self.goal.refresh_from_db()
        self.assertEqual(self.goal.status, Goal.STATUS_DRAFT)

    def test_goal_complete_by_other_user_forbidden(self):
        """Тест завершения цели не владельцем (должно быть запрещено)"""
        # Меняем статус цели на "В процессе"
        self.goal.status = Goal.STATUS_IN_PROGRESS
        self.goal.save()

        self.client.force_authenticate(user=self.__class__.employee2_user)

        response = self.client.post(self.goal_complete_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Проверяем, что статус цели не изменился
        self.goal.refresh_from_db()
        self.assertEqual(self.goal.status, Goal.STATUS_IN_PROGRESS)


class GoalFilteringTestCase(APITestCase):
    """Тесты фильтрации списка целей"""

    @classmethod
    def setUpTestData(cls):
        """Создание данных для всех тестов"""
        today = timezone.now().date()
        past_date = today - timedelta(days=90)

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

        # Базовые данные для целей
        cls.goal_data = {
            'employee': cls.employee,
            'start_period': today,
            'end_period': today + timedelta(days=30),
        }

        cls.past_goal_data = {
            'employee': cls.employee,
            'start_period': past_date,
            'end_period': past_date + timedelta(days=30),
            'status': Goal.STATUS_IN_PROGRESS,
        }

        # URL для списка целей
        cls.goals_url = reverse('goal-list')

    def setUp(self):
        """Подготовка данных перед каждым тестом"""
        # Создаем цели в разных статусах
        self.draft_goal = Goal.objects.create(
            title='Draft Goal',
            description='Draft Description',
            expected_results='Draft Expected Results',
            status=Goal.STATUS_DRAFT,
            **self.__class__.goal_data
        )

        self.pending_goal = Goal.objects.create(
            title='Pending Goal',
            description='Pending Description',
            expected_results='Pending Expected Results',
            status=Goal.STATUS_PENDING_APPROVAL,
            **self.__class__.goal_data
        )

        self.progress_goal = Goal.objects.create(
            title='In Progress Goal',
            description='In Progress Description',
            expected_results='In Progress Expected Results',
            status=Goal.STATUS_IN_PROGRESS,
            **self.__class__.goal_data
        )

        self.assessment_goal = Goal.objects.create(
            title='Assessment Goal',
            description='Assessment Description',
            expected_results='Assessment Expected Results',
            status=Goal.STATUS_PENDING_ASSESSMENT,
            **self.__class__.goal_data
        )

        # Создаем цель с другим периодом
        self.past_goal = Goal.objects.create(
            title='Past Goal',
            description='Past Description',
            expected_results='Past Expected Results',
            **self.__class__.past_goal_data
        )

    def test_filter_goals_by_status(self):
        """Тест фильтрации целей по статусу"""
        self.client.force_authenticate(user=self.__class__.employee_user)

        # Фильтрация по одному статусу
        response = self.client.get(
            f"{self.__class__.goals_url}?status={Goal.STATUS_DRAFT}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Draft Goal')

        # Фильтрация по нескольким статусам
        response = self.client.get(
            f"{self.__class__.goals_url}?status={Goal.STATUS_DRAFT},{Goal.STATUS_IN_PROGRESS}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data),
                         3)  # 1 черновик + 2 в процессе (включая прошлую)

    def test_filter_goals_by_period(self):
        """Тест фильтрации целей по периоду"""
        self.client.force_authenticate(user=self.__class__.employee_user)

        # Фильтрация по периоду start_period
        today = timezone.now().date().isoformat()
        response = self.client.get(
            f"{self.__class__.goals_url}?start_period={today}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)  # Все кроме прошлой цели

        # Фильтрация по периоду end_period
        past_date = (timezone.now().date() - timedelta(days=60)).isoformat()
        response = self.client.get(
            f"{self.__class__.goals_url}?end_period={past_date}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Только прошлая цель

    def test_filter_goals_by_title(self):
        """Тест фильтрации целей по названию"""
        self.client.force_authenticate(user=self.__class__.employee_user)

        response = self.client.get(f"{self.__class__.goals_url}?search=Draft")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Draft Goal')

        response = self.client.get(f"{self.__class__.goals_url}?search=Goal")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)  # Все цели

    def test_combined_filtering(self):
        """Тест комбинированной фильтрации целей"""
        self.client.force_authenticate(user=self.__class__.employee_user)

        # Комбинируем фильтры
        today = timezone.now().date().isoformat()
        response = self.client.get(
            f"{self.__class__.goals_url}?status={Goal.STATUS_IN_PROGRESS}&start_period={today}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data),
                         1)  # Только текущая цель в процессе
        self.assertEqual(response.data[0]['title'], 'In Progress Goal')
