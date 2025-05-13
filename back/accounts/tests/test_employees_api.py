from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User, Employee


class EmployeeAPITests(TestCase):
    """Тесты API сотрудников выделены в отдельный класс"""

    @classmethod
    def setUpTestData(cls):
        """Создаем базовые данные для всех тестов класса"""
        # Создаем администратора
        cls.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='password123',
            first_name='Admin',
            last_name='User',
            role='admin'
        )

        # Создаем руководителя отдела
        cls.leader_user = User.objects.create_user(
            username='leader',
            email='leader@example.com',
            password='password123',
            first_name='Leader',
            last_name='User',
            role='expertise_leader'
        )

        cls.leader = Employee.objects.create(
            user=cls.leader_user,
            hire_dt='2019-01-01',
            position='Department Lead'
        )

        # Создаем менеджера команды
        cls.manager_user = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='password123',
            first_name='Manager',
            last_name='User',
            role='employee'
        )

        cls.manager = Employee.objects.create(
            user=cls.manager_user,
            hire_dt='2020-01-01',
            position='Team Lead',
            manager=cls.leader
        )

        # Создаем обычного сотрудника
        cls.employee_user = User.objects.create_user(
            username='employee',
            email='employee@example.com',
            password='password123',
            first_name='Test',
            last_name='User',
            role='employee'
        )

        cls.employee = Employee.objects.create(
            user=cls.employee_user,
            hire_dt='2021-01-01',
            position='Developer',
            manager=cls.manager
        )

        # Создаем второго сотрудника
        cls.employee2_user = User.objects.create_user(
            username='employee2',
            email='employee2@example.com',
            password='password123',
            first_name='Second',
            last_name='Employee',
            role='employee'
        )

        cls.employee2 = Employee.objects.create(
            user=cls.employee2_user,
            hire_dt='2021-02-01',
            position='QA Engineer',
            manager=cls.manager
        )

        # Пользователь без профиля сотрудника
        cls.user_without_profile = User.objects.create_user(
            username='noemployee',
            email='noemployee@example.com',
            password='password123',
            first_name='No',
            last_name='Profile',
            role='employee'
        )

        # Запоминаем начальное количество сотрудников
        cls.initial_employee_count = Employee.objects.count()

    def setUp(self):
        """Подготовка для каждого теста"""
        self.client = APIClient()

    def test_employee_list_any_user_allowed(self):
        """Тест доступа любого пользователя к списку сотрудников"""
        self.client.force_authenticate(user=self.employee_user)
        url = reverse('employee-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), self.initial_employee_count)

    def test_employee_create_admin_allowed(self):
        """Тест создания профиля сотрудника администратором"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('employee-list')
        data = {
            'user_id': self.user_without_profile.id,
            'hire_dt': '2022-01-01',
            'position': 'Product Manager',
            'manager': self.manager.id
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['position'], 'Product Manager')
        self.assertTrue(
            Employee.objects.filter(
                user_id=self.user_without_profile.id).exists()
        )
        self.assertEqual(Employee.objects.count(),
                         self.initial_employee_count + 1)

    def test_employee_create_duplicate_user(self):
        """Тест создания профиля для пользователя, у которого уже есть профиль"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('employee-list')
        data = {
            'user_id': self.employee_user.id,
            # у этого пользователя уже есть профиль
            'hire_dt': '2022-01-01',
            'position': 'Product Manager',
            'manager': self.manager.id
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('user_id', response.data)

    def test_employee_create_invalid_user_id(self):
        """Тест создания профиля с несуществующим ID пользователя"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('employee-list')
        data = {
            'user_id': 9999,  # несуществующий ID
            'hire_dt': '2022-01-01',
            'position': 'Product Manager',
            'manager': self.manager.id
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('user_id', response.data)

    def test_employee_create_employee_forbidden(self):
        """Тест запрета создания профиля сотрудника обычным пользователем"""
        self.client.force_authenticate(user=self.employee_user)
        url = reverse('employee-list')
        data = {
            'user_id': self.user_without_profile.id,
            'hire_dt': '2022-01-01',
            'position': 'Product Manager',
            'manager': self.manager.id
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_employee_retrieve_any_user_allowed(self):
        """Тест доступа любого пользователя к информации о любом сотруднике"""
        self.client.force_authenticate(user=self.employee_user)
        url = reverse('employee-detail', kwargs={'pk': self.manager.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['position'], 'Team Lead')
        self.assertTrue(
            'subordinates' in response.data)  # в детальном представлении есть подчиненные

    def test_employee_update_admin_allowed(self):
        """Тест обновления профиля сотрудника администратором"""
        original_position = self.employee.position

        self.client.force_authenticate(user=self.admin_user)
        url = reverse('employee-detail', kwargs={'pk': self.employee.id})
        data = {
            'position': 'Senior Developer',
            'hire_dt': '2021-01-01'
        }
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Перезагружаем объект из БД для проверки обновления
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.position, 'Senior Developer')
        self.assertNotEqual(self.employee.position, original_position)

    def test_employee_update_self_allowed(self):
        """Тест обновления сотрудником своего профиля"""
        original_position = self.employee.position

        self.client.force_authenticate(user=self.employee_user)
        url = reverse('employee-detail', kwargs={'pk': self.employee.id})
        data = {
            'position': 'Senior Developer',
            'hire_dt': '2021-01-01'
        }
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Перезагружаем объект из БД для проверки обновления
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.position, 'Senior Developer')
        self.assertNotEqual(self.employee.position, original_position)

    def test_employee_update_other_forbidden(self):
        """Тест запрета обновления сотрудником профиля другого сотрудника"""
        original_position = self.employee2.position

        self.client.force_authenticate(user=self.employee_user)
        url = reverse('employee-detail', kwargs={'pk': self.employee2.id})
        data = {
            'position': 'Changed Position'
        }
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Проверяем, что данные не изменились
        self.employee2.refresh_from_db()
        self.assertEqual(self.employee2.position, original_position)

    def test_employee_delete_admin_allowed(self):
        """Тест удаления профиля сотрудника администратором"""
        # Запоминаем ID для проверки после удаления
        employee_id = self.employee.id
        user_id = self.employee_user.id

        self.client.force_authenticate(user=self.admin_user)
        url = reverse('employee-detail', kwargs={'pk': employee_id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Employee.objects.filter(id=employee_id).exists())
        self.assertTrue(User.objects.filter(
            id=user_id).exists())  # пользователь должен остаться

    def test_employee_delete_self_forbidden(self):
        """Тест запрета удаления сотрудником своего профиля"""
        employee_id = self.employee.id

        self.client.force_authenticate(user=self.employee_user)
        url = reverse('employee-detail', kwargs={'pk': employee_id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Employee.objects.filter(id=employee_id).exists())

    def test_employee_my_profile_success(self):
        """Тест получения информации о своем профиле сотрудника"""
        self.client.force_authenticate(user=self.employee_user)
        url = reverse('employee-my-profile')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['position'], 'Developer')
        self.assertEqual(response.data['manager_name'], 'Manager User')
        self.assertEqual(response.data['user']['username'], 'employee')

    def test_employee_my_profile_not_found(self):
        """Тест получения профиля для пользователя без профиля сотрудника"""
        self.client.force_authenticate(user=self.user_without_profile)
        url = reverse('employee-my-profile')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('detail', response.data)

    def test_employee_my_team_manager(self):
        """Тест получения списка прямых подчиненных менеджером"""
        self.client.force_authenticate(user=self.manager_user)
        url = reverse('employee-my-team')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Менеджер имеет 2 прямых подчиненных (employee и employee2)
        direct_subordinates = Employee.objects.filter(
            manager=self.manager).count()
        self.assertEqual(len(response.data), direct_subordinates)

    def test_employee_my_team_with_levels(self):
        """Тест получения списка подчиненных на всех уровнях иерархии"""
        # Создаем сотрудника третьего уровня только для этого теста
        level3_user = User.objects.create_user(
            username='level3_test_only',
            email='level3_test@example.com',
            password='password123',
            first_name='Level3',
            last_name='User',
            role='employee'
        )

        level3_employee = Employee.objects.create(
            user=level3_user,
            hire_dt='2022-01-01',
            position='Junior Developer',
            manager=self.employee  # Подчиняется employee
        )

        # Теперь у нас иерархия: leader -> manager -> employee -> level3_employee
        # и manager -> employee2

        self.client.force_authenticate(user=self.leader_user)
        url = f"{reverse('employee-my-team')}?levels=3"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # leader должен видеть все 4 уровня подчиненных:
        # manager, employee, employee2, level3_employee
        expected_subordinates = 4  # все подчиненные включая вложенные уровни
        self.assertEqual(len(response.data), expected_subordinates)

        # Проверяем, что среди результатов есть все позиции
        positions = set(item['position'] for item in response.data)
        expected_positions = {'Team Lead', 'Developer', 'QA Engineer',
                              'Junior Developer'}
        self.assertEqual(positions, expected_positions)

    def test_employee_my_team_no_employees(self):
        """Тест получения списка подчиненных сотрудником без подчиненных"""
        self.client.force_authenticate(user=self.employee_user)
        url = reverse('employee-my-team')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # нет подчиненных

    def test_employee_my_team_not_found(self):
        """Тест получения списка подчиненных пользователем без профиля сотрудника"""
        self.client.force_authenticate(user=self.user_without_profile)
        url = reverse('employee-my-team')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('detail', response.data)


class EmployeeTeamRecursiveTests(TestCase):
    """Отдельный класс для тестирования сложных иерархий в командах"""

    @classmethod
    def setUpTestData(cls):
        """Создаем сложную иерархию сотрудников для тестирования"""
        # Создаем директора
        cls.director_user = User.objects.create_user(
            username='director',
            email='director@example.com',
            password='password123',
            first_name='Director',
            last_name='User',
            role='expertise_leader'
        )

        cls.director = Employee.objects.create(
            user=cls.director_user,
            hire_dt='2018-01-01',
            position='Director'
        )

        # Создаем 2 руководителей отделов
        cls.head1_user = User.objects.create_user(
            username='head1',
            email='head1@example.com',
            password='password123',
            first_name='Head1',
            last_name='User',
            role='expertise_leader'
        )

        cls.head1 = Employee.objects.create(
            user=cls.head1_user,
            hire_dt='2019-01-01',
            position='Department Head 1',
            manager=cls.director
        )

        cls.head2_user = User.objects.create_user(
            username='head2',
            email='head2@example.com',
            password='password123',
            first_name='Head2',
            last_name='User',
            role='expertise_leader'
        )

        cls.head2 = Employee.objects.create(
            user=cls.head2_user,
            hire_dt='2019-02-01',
            position='Department Head 2',
            manager=cls.director
        )

        # Создаем менеджеров команд для каждого отдела
        cls.manager1_user = User.objects.create_user(
            username='manager1',
            email='manager1@example.com',
            password='password123',
            first_name='Manager1',
            last_name='User',
            role='employee'
        )

        cls.manager1 = Employee.objects.create(
            user=cls.manager1_user,
            hire_dt='2020-01-01',
            position='Team Lead 1',
            manager=cls.head1
        )

        cls.manager2_user = User.objects.create_user(
            username='manager2',
            email='manager2@example.com',
            password='password123',
            first_name='Manager2',
            last_name='User',
            role='employee'
        )

        cls.manager2 = Employee.objects.create(
            user=cls.manager2_user,
            hire_dt='2020-02-01',
            position='Team Lead 2',
            manager=cls.head2
        )

        # Создаем сотрудников для каждой команды
        cls.dev1_user = User.objects.create_user(
            username='dev1',
            email='dev1@example.com',
            password='password123',
            first_name='Dev1',
            last_name='User',
            role='employee'
        )

        cls.dev1 = Employee.objects.create(
            user=cls.dev1_user,
            hire_dt='2021-01-01',
            position='Developer 1',
            manager=cls.manager1
        )

        cls.dev2_user = User.objects.create_user(
            username='dev2',
            email='dev2@example.com',
            password='password123',
            first_name='Dev2',
            last_name='User',
            role='employee'
        )

        cls.dev2 = Employee.objects.create(
            user=cls.dev2_user,
            hire_dt='2021-02-01',
            position='Developer 2',
            manager=cls.manager1
        )

        cls.qa1_user = User.objects.create_user(
            username='qa1',
            email='qa1@example.com',
            password='password123',
            first_name='QA1',
            last_name='User',
            role='employee'
        )

        cls.qa1 = Employee.objects.create(
            user=cls.qa1_user,
            hire_dt='2021-03-01',
            position='QA 1',
            manager=cls.manager2
        )

        cls.qa2_user = User.objects.create_user(
            username='qa2',
            email='qa2@example.com',
            password='password123',
            first_name='QA2',
            last_name='User',
            role='employee'
        )

        cls.qa2 = Employee.objects.create(
            user=cls.qa2_user,
            hire_dt='2021-04-01',
            position='QA 2',
            manager=cls.manager2
        )

        # Создаем младших сотрудников (уровень 4)
        cls.junior_user = User.objects.create_user(
            username='junior',
            email='junior@example.com',
            password='password123',
            first_name='Junior',
            last_name='Dev',
            role='employee'
        )

        cls.junior = Employee.objects.create(
            user=cls.junior_user,
            hire_dt='2022-01-01',
            position='Junior Developer',
            manager=cls.dev1
        )

    def setUp(self):
        self.client = APIClient()

    def test_director_sees_all_team(self):
        """Тест получения директором всех подчиненных на всех уровнях"""
        self.client.force_authenticate(user=self.director_user)
        url = f"{reverse('employee-my-team')}?levels=4"  # 4 уровня иерархии
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Директор должен видеть всех 9 подчиненных:
        # 2 руководителя отделов + 2 тимлида + 4 разработчика/тестировщика + 1 младший
        expected_subordinates = 9
        self.assertEqual(len(response.data), expected_subordinates)

        # Проверяем, что среди подчиненных есть представители всех уровней
        usernames = [item['user']['username'] for item in response.data]

        # Проверка репрезентативных пользователей из каждого уровня
        self.assertIn('head1', usernames)  # уровень 1
        self.assertIn('manager1', usernames)  # уровень 2
        self.assertIn('dev1', usernames)  # уровень 3
        self.assertIn('junior', usernames)  # уровень 4

    def test_department_head_sees_limited_team(self):
        """Тест получения руководителем отдела своих подчиненных с ограничением уровней"""
        self.client.force_authenticate(user=self.head1_user)
        url = f"{reverse('employee-my-team')}?levels=1"  # только прямые подчиненные
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Head1 должен видеть только 1 прямого подчиненного: manager1
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['user']['username'], 'manager1')

        # Теперь проверяем с глубиной 2 уровня
        url = f"{reverse('employee-my-team')}?levels=2"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Head1 должен видеть 3 подчиненных: manager1 + dev1 + dev2
        self.assertEqual(len(response.data), 3)

        usernames = [item['user']['username'] for item in response.data]
        self.assertIn('manager1', usernames)
        self.assertIn('dev1', usernames)
        self.assertIn('dev2', usernames)

        # Теперь проверяем с глубиной 3 уровня
        url = f"{reverse('employee-my-team')}?levels=3"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Head1 должен видеть 4 подчиненных: manager1 + dev1 + dev2 + junior
        self.assertEqual(len(response.data), 4)

        usernames = [item['user']['username'] for item in response.data]
        self.assertIn('junior', usernames)

    def test_different_managers_see_different_teams(self):
        """Тест что разные менеджеры видят только своих подчиненных"""
        # Тест для manager1
        self.client.force_authenticate(user=self.manager1_user)
        url = reverse('employee-my-team')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # manager1 должен видеть 2 прямых подчиненных: dev1 и dev2
        self.assertEqual(len(response.data), 2)

        usernames = [item['user']['username'] for item in response.data]
        self.assertIn('dev1', usernames)
        self.assertIn('dev2', usernames)
        self.assertNotIn('qa1', usernames)  # qa1 не в команде manager1

        # Тест для manager2
        self.client.force_authenticate(user=self.manager2_user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # manager2 должен видеть 2 прямых подчиненных: qa1 и qa2
        self.assertEqual(len(response.data), 2)

        usernames = [item['user']['username'] for item in response.data]
        self.assertIn('qa1', usernames)
        self.assertIn('qa2', usernames)
        self.assertNotIn('dev1', usernames)  # dev1 не в команде manager2

    def test_recursive_team_query_performance(self):
        """Тест производительности рекурсивного запроса команды"""
        # Этот тест проверяет, что рекурсивный запрос не делает слишком много SQL запросов

        from django.db import connection, reset_queries
        import time

        # Включаем отслеживание запросов
        reset_queries()

        # Измеряем время выполнения запроса команды директора
        self.client.force_authenticate(user=self.director_user)
        url = f"{reverse('employee-my-team')}?levels=4"

        start_time = time.time()
        response = self.client.get(url)
        end_time = time.time()

        # Проверяем успешность запроса
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем количество запросов (должно быть оптимизировано)
        query_count = len(connection.queries)

        # Проверяем время выполнения (должно быть быстрым)
        execution_time = end_time - start_time

        # Выводим информацию о производительности для анализа
        print(
            f"\nTeam query performance: {query_count} queries, {execution_time:.4f} seconds")

        # Проверка для такой сложной иерархии должна быть в пределах разумного
        self.assertLess(query_count, 30,
                        "Слишком много SQL запросов для получения команды")
        self.assertLess(execution_time, 1.0,
                        "Запрос команды слишком долгий")
