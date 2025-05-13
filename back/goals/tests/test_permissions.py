from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User, Employee
from goals.models import Goal


class PermissionTestMixin:
    """Миксин для создания общих объектов для всех тестов прав доступа"""

    @classmethod
    def setUpTestData(cls):
        """Создание общих тестовых данных для всех тестов"""
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

        # Создаем сотрудника с руководителем
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

        # Создаем сотрудника без связи с первым
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
            hire_dt=today
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

        # Общие данные для целей
        cls.goal_data = {
            'employee': cls.employee,
            'title': 'Test Goal',
            'description': 'Test Description',
            'expected_results': 'Test Expected Results',
            'start_period': today,
            'end_period': end_date,
        }


class PermissionsTestCase(PermissionTestMixin, APITestCase):
    """Тесты проверки прав доступа"""

    def setUp(self):
        """Создание тестовой цели перед каждым тестом"""
        self.goal = Goal.objects.create(
            status=Goal.STATUS_DRAFT,
            **self.__class__.goal_data
        )

    def test_is_employee_owner_or_manager_or_admin_permission(self):
        """Тест разрешения IsEmployeeOwnerOrManagerOrAdmin"""
        from goals.permissions import \
            IsEmployeeOwnerOrManagerOrExpertiseLeaderOrAdmin

        permission = IsEmployeeOwnerOrManagerOrExpertiseLeaderOrAdmin()

        # Проверка для владельца цели
        request = type('Request', (), {'user': self.__class__.employee_user})()
        self.assertTrue(
            permission.has_object_permission(request, None, self.goal))

        # Проверка для руководителя
        request = type('Request', (), {'user': self.__class__.manager_user})()
        self.assertTrue(
            permission.has_object_permission(request, None, self.goal))

        # Проверка для администратора
        request = type('Request', (), {'user': self.__class__.admin_user})()
        self.assertTrue(
            permission.has_object_permission(request, None, self.goal))

        # Проверка для другого сотрудника
        request = type('Request', (),
                       {'user': self.__class__.employee2_user})()
        self.assertFalse(
            permission.has_object_permission(request, None, self.goal))

    def test_is_manager_permission(self):
        """Тест разрешения IsManager"""
        from goals.permissions import IsManager

        permission = IsManager()

        # Проверка для руководителя
        request = type('Request', (), {'user': self.__class__.manager_user})()
        self.assertTrue(permission.has_permission(request, None))

        # Проверка для сотрудника без подчиненных
        request = type('Request', (), {'user': self.__class__.employee_user})()
        self.assertFalse(permission.has_permission(request, None))

        # Проверка для руководителя цели
        request = type('Request', (), {'user': self.__class__.manager_user})()
        self.assertTrue(
            permission.has_object_permission(request, None, self.goal)
        )

        # Проверка для руководителя не являющегося руководителем сотрудника
        employee = self.__class__.employee
        employee.manager = None
        employee.save()
        self.assertFalse(
            permission.has_object_permission(request, None, self.goal))

        # Восстанавливаем руководителя для других тестов
        employee.manager = self.__class__.manager
        employee.save()

    def test_is_expertise_leader_permission(self):
        """Тест разрешения IsExpertiseLeader"""
        from goals.permissions import IsExpertiseLeader

        permission = IsExpertiseLeader()

        # Проверка для лидера профессии
        request = type('Request', (),
                       {'user': self.__class__.expertise_leader_user})()
        self.assertTrue(permission.has_permission(request, None))

        # Проверка для руководителя
        request = type('Request', (), {'user': self.__class__.manager_user})()
        self.assertFalse(permission.has_permission(request, None))

        # Проверка для сотрудника
        request = type('Request', (), {'user': self.__class__.employee_user})()
        self.assertFalse(permission.has_permission(request, None))

    def test_can_manage_goal_permission(self):
        """Тест разрешения CanManageGoal"""
        from goals.permissions import CanManageGoal

        permission = CanManageGoal()

        # Создаем объекты для тестирования
        view = type('View', (), {})()
        view.action = 'retrieve'  # SAFE_METHOD
        request = type('Request', (),
                       {'user': self.__class__.employee_user,
                        'method': 'GET'})()

        # Проверка чтения владельцем цели
        self.assertTrue(
            permission.has_object_permission(request, view, self.goal))

        # Проверка чтения руководителем цели
        request.user = self.__class__.manager_user
        self.assertTrue(
            permission.has_object_permission(request, view, self.goal))

        # Проверка чтения другим сотрудником (должно быть запрещено)
        request.user = self.__class__.employee2_user
        self.assertFalse(
            permission.has_object_permission(request, view, self.goal))

        # Проверка редактирования владельцем черновика
        view.action = 'update'
        request.user = self.__class__.employee_user
        request.method = 'PUT'
        self.assertTrue(
            permission.has_object_permission(request, view, self.goal))

        # Проверка редактирования не владельцем (должно быть запрещено)
        request.user = self.__class__.manager_user
        self.assertFalse(
            permission.has_object_permission(request, view, self.goal))

        # Проверка отправки на согласование владельцем
        view.action = 'submit'
        request.user = self.__class__.employee_user
        self.assertTrue(
            permission.has_object_permission(request, view, self.goal))

        # Проверка согласования руководителем
        self.goal.status = Goal.STATUS_PENDING_APPROVAL
        self.goal.save()

        view.action = 'approve'
        request.user = self.__class__.manager_user
        self.assertTrue(
            permission.has_object_permission(request, view, self.goal))

        # Проверка согласования не руководителем (должно быть запрещено)
        request.user = self.__class__.employee2_user
        self.assertFalse(
            permission.has_object_permission(request, view, self.goal))

        # Проверка завершения цели владельцем
        self.goal.status = Goal.STATUS_IN_PROGRESS
        self.goal.save()

        view.action = 'complete'
        request.user = self.__class__.employee_user
        self.assertTrue(
            permission.has_object_permission(request, view, self.goal))

        # Проверка завершения цели не владельцем (должно быть запрещено)
        request.user = self.__class__.employee2_user
        self.assertFalse(
            permission.has_object_permission(request, view, self.goal))


class PermissionsIntegrationTestCase(PermissionTestMixin, APITestCase):
    """Интеграционные тесты проверки прав доступа при различных сценариях"""

    def setUp(self):
        """Создание организационной структуры и целей для тестирования"""
        # Директор
        self.director_user = User.objects.create_user(
            username='director',
            password='password123',
            email='director@example.com',
            first_name='Director',
            last_name='User',
            role='manager'
        )
        self.director = Employee.objects.create(
            user=self.director_user,
            position='Director',
            hire_dt=timezone.now().date()
        )

        # Руководитель отдела 1
        self.head1_user = User.objects.create_user(
            username='head1',
            password='password123',
            email='head1@example.com',
            first_name='Head1',
            last_name='User',
            role='manager'
        )
        self.head1 = Employee.objects.create(
            user=self.head1_user,
            position='Department Head',
            hire_dt=timezone.now().date(),
            manager=self.director
        )

        # Менеджер команды 1
        self.manager1_user = User.objects.create_user(
            username='manager1',
            password='password123',
            email='manager1@example.com',
            first_name='Manager1',
            last_name='User',
            role='manager'
        )
        self.manager1 = Employee.objects.create(
            user=self.manager1_user,
            position='Team Lead',
            hire_dt=timezone.now().date(),
            manager=self.head1
        )

        # Разработчик в команде 1
        self.dev1_user = User.objects.create_user(
            username='dev1',
            password='password123',
            email='dev1@example.com',
            first_name='Dev1',
            last_name='User',
            role='employee'
        )
        self.dev1 = Employee.objects.create(
            user=self.dev1_user,
            position='Developer',
            hire_dt=timezone.now().date(),
            manager=self.manager1
        )

        # Руководитель отдела 2
        self.head2_user = User.objects.create_user(
            username='head2',
            password='password123',
            email='head2@example.com',
            first_name='Head2',
            last_name='User',
            role='manager'
        )
        self.head2 = Employee.objects.create(
            user=self.head2_user,
            position='Department Head',
            hire_dt=timezone.now().date(),
            manager=self.director
        )

        # Обновляем руководителя для лидера профессии
        self.__class__.expertise_leader.manager = self.head2
        self.__class__.expertise_leader.save()

        # Создаем общие данные для тестовых целей без заголовка
        today = timezone.now().date()
        end_date = today + timedelta(days=30)
        self.test_goal_base_data = {
            'description': 'Test Description',
            'expected_results': 'Test Expected Results',
            'start_period': today,
            'end_period': end_date,
        }

        # Создаем цели для разных сотрудников в разных статусах
        # Цель для разработчика в статусе черновика
        self.draft_goal = Goal.objects.create(
            employee=self.dev1,
            title='Draft Goal',
            status=Goal.STATUS_DRAFT,
            **self.test_goal_base_data
        )

        # Цель для разработчика на согласовании
        self.pending_goal = Goal.objects.create(
            employee=self.dev1,
            title='Pending Goal',
            status=Goal.STATUS_PENDING_APPROVAL,
            **self.test_goal_base_data
        )

        # Цель для разработчика в процессе
        self.in_progress_goal = Goal.objects.create(
            employee=self.dev1,
            title='In Progress Goal',
            status=Goal.STATUS_IN_PROGRESS,
            **self.test_goal_base_data
        )

        # Цель для разработчика ожидающая оценки
        self.assessment_goal = Goal.objects.create(
            employee=self.dev1,
            title='Assessment Goal',
            status=Goal.STATUS_PENDING_ASSESSMENT,
            **self.test_goal_base_data
        )

        # Цель для лидера профессии в процессе
        self.leader_goal = Goal.objects.create(
            employee=self.__class__.expertise_leader,
            title='Leader Goal',
            status=Goal.STATUS_IN_PROGRESS,
            **self.test_goal_base_data
        )

    def test_goal_visibility_chain_of_command(self):
        """Тест видимости целей по цепочке управления"""

        # URL для списка целей
        goals_url = reverse('goal-list')

        # Сотрудник видит только свои цели (4)
        self.client.force_authenticate(user=self.dev1_user)
        response = self.client.get(goals_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

        # Непосредственный руководитель видит цели подчиненных (4)
        self.client.force_authenticate(user=self.manager1_user)
        response = self.client.get(goals_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

        # Руководитель отдела видит цели всех в своей структуре (4)
        self.client.force_authenticate(user=self.head1_user)
        response = self.client.get(goals_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

        # Директор видит цели всей организации (5)
        self.client.force_authenticate(user=self.director_user)
        response = self.client.get(goals_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)

        # Лидер профессии видит свои цели (1) + цели на оценке (1)
        self.client.force_authenticate(
            user=self.__class__.expertise_leader_user)
        response = self.client.get(goals_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        # Руководитель другого отдела не видит цели не своих сотрудников
        # (видит только цель лидера профессии, который в его отделе)
        self.client.force_authenticate(user=self.head2_user)
        response = self.client.get(goals_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        # Администратор видит все цели (5)
        self.client.force_authenticate(user=self.__class__.admin_user)
        response = self.client.get(goals_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)

    def test_goal_workflow_complete_scenario(self):
        """Интеграционный тест полного жизненного цикла цели"""

        # 1. Сотрудник создает новую цель
        self.client.force_authenticate(user=self.dev1_user)

        data = {
            'title': 'New Workflow Goal',
            'description': 'Test Workflow Description',
            'expected_results': 'Test Workflow Expected Results',
            'start_period': timezone.now().date().isoformat(),
            'end_period': (timezone.now().date() + timedelta(
                days=30)).isoformat(),
        }

        response = self.client.post(reverse('goal-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertIn('id', response.data, "ID not found in response data")
        goal_id = response.data['id']

        goal_detail_url = reverse('goal-detail', kwargs={'pk': goal_id})
        goal_submit_url = reverse('goal-submit', kwargs={'pk': goal_id})
        goal_approve_url = reverse('goal-approve', kwargs={'pk': goal_id})
        goal_complete_url = reverse('goal-complete', kwargs={'pk': goal_id})
        progress_url = reverse('goal-progress-list',
                               kwargs={'goal_pk': goal_id})
        self_assessment_url = reverse('goal-self-assessment-list',
                                      kwargs={'goal_pk': goal_id})

        # 2. Сотрудник отправляет цель на согласование
        response = self.client.post(goal_submit_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 3. Попытка создать прогресс до одобрения цели должна быть отклонена
        progress_data = {
            'description': 'Early Progress Update'
        }
        response = self.client.post(progress_url, progress_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # 4. Руководитель согласовывает цель
        self.client.force_authenticate(user=self.manager1_user)
        response = self.client.post(goal_approve_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 5. Сотрудник может создавать записи о прогрессе
        self.client.force_authenticate(user=self.dev1_user)

        progress_data = {
            'description': 'First Progress Update'
        }
        response = self.client.post(progress_url, progress_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        progress_data = {
            'description': 'Second Progress Update'
        }
        response = self.client.post(progress_url, progress_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 6. Руководитель может видеть и создавать записи о прогрессе
        self.client.force_authenticate(user=self.manager1_user)

        response = self.client.get(progress_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        progress_data = {
            'description': 'Manager Progress Update'
        }
        response = self.client.post(progress_url, progress_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 7. Сотрудник добавляет самооценку еще до завершения
        self.client.force_authenticate(user=self.dev1_user)

        assessment_data = {
            'rating': 7,
            'comments': 'Self Assessment Comments',
            'areas_to_improve': 'Areas to Improve'
        }
        response = self.client.post(self_assessment_url, assessment_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 8. Сотрудник отмечает цель как завершенную
        response = self.client.post(goal_complete_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 9. Попытка создания нового прогресса должна быть отклонена
        progress_data = {
            'description': 'Late Progress Update'
        }
        response = self.client.post(progress_url, progress_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # 10. Лидер профессии может видеть цель, ожидающую оценки
        self.client.force_authenticate(
            user=self.__class__.expertise_leader_user)

        response = self.client.get(goal_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 11. Лидер профессии может видеть, но не редактировать самооценку
        assessment_id = response.data['self_assessment']['id']
        assessment_detail_url = reverse(
            'goal-self-assessment-detail',
            kwargs={
                'goal_pk': goal_id,
                'pk': assessment_id
            }
        )

        response = self.client.get(assessment_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        assessment_data = {
            'rating': 8,
            'comments': 'Updated by Leader',
            'areas_to_improve': 'Leader Suggestions'
        }
        response = self.client.patch(assessment_detail_url, assessment_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 12. Администратор видит всю информацию о цикле
        self.client.force_authenticate(user=self.__class__.admin_user)

        response = self.client.get(goal_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'],
                         Goal.STATUS_PENDING_ASSESSMENT)
        self.assertEqual(len(response.data['progress_updates']), 3)
        self.assertEqual(response.data['self_assessment']['rating'], 7)
