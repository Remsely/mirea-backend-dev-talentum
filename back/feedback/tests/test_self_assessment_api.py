from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User, Employee
from goals.models import Goal
from feedback.models import SelfAssessment


class SelfAssessmentAPITestCase(APITestCase):
    """Тесты API для самооценки"""

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

        # Создаем сотрудников
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

        # Создаем цели в разных статусах
        cls.in_progress_goal = Goal.objects.create(
            employee=cls.employee,
            title='In Progress Goal',
            description='In Progress Description',
            expected_results='In Progress Expected Results',
            start_period=today,
            end_period=end_date,
            status=Goal.STATUS_IN_PROGRESS
        )

        cls.pending_assessment_goal = Goal.objects.create(
            employee=cls.employee,
            title='Pending Assessment Goal',
            description='Pending Assessment Description',
            expected_results='Pending Assessment Expected Results',
            start_period=today,
            end_period=end_date,
            status=Goal.STATUS_PENDING_ASSESSMENT
        )

        # Создаем цель для другого сотрудника
        cls.other_goal = Goal.objects.create(
            employee=cls.employee2,
            title='Other Goal',
            description='Other Description',
            expected_results='Other Expected Results',
            start_period=today,
            end_period=end_date,
            status=Goal.STATUS_IN_PROGRESS
        )

    def setUp(self):
        """Настройка перед каждым тестом"""
        # URL-адреса для тестов
        self.in_progress_self_assessment_url = reverse(
            'goal-self-assessment-list',
            kwargs={'goal_pk': self.__class__.in_progress_goal.pk}
        )
        self.pending_assessment_self_assessment_url = reverse(
            'goal-self-assessment-list',
            kwargs={'goal_pk': self.__class__.pending_assessment_goal.pk}
        )
        self.other_self_assessment_url = reverse(
            'goal-self-assessment-list',
            kwargs={'goal_pk': self.__class__.other_goal.pk}
        )

    def test_self_assessment_create_success(self):
        """Тест успешного создания самооценки"""
        self.client.force_authenticate(user=self.__class__.employee_user)

        data = {
            'rating': 8,
            'comments': 'Хорошо справился с поставленной задачей',
            'areas_to_improve': 'Нужно улучшить управление временем'
        }

        response = self.client.post(self.in_progress_self_assessment_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['rating'], 8)
        self.assertEqual(SelfAssessment.objects.count(), 1)

        created_assessment = SelfAssessment.objects.first()
        self.assertEqual(created_assessment.goal, self.__class__.in_progress_goal)
        self.assertEqual(created_assessment.rating, 8)

    def test_self_assessment_create_by_other_user_forbidden(self):
        """Тест запрета создания самооценки другим сотрудником"""
        self.client.force_authenticate(user=self.__class__.employee2_user)

        data = {
            'rating': 7,
            'comments': 'Unauthorized assessment',
            'areas_to_improve': 'This should not work'
        }

        response = self.client.post(self.in_progress_self_assessment_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(SelfAssessment.objects.count(), 0)

    def test_self_assessment_create_by_manager_allowed(self):
        """Тест создания самооценки руководителем"""
        self.client.force_authenticate(user=self.__class__.manager_user)

        data = {
            'rating': 9,
            'comments': 'Manager assessment',
            'areas_to_improve': 'Areas from manager'
        }

        response = self.client.post(self.in_progress_self_assessment_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SelfAssessment.objects.count(), 1)

    def test_self_assessment_update_success(self):
        """Тест успешного обновления самооценки"""
        # Создаем самооценку
        self_assessment = SelfAssessment.objects.create(
            goal=self.__class__.in_progress_goal,
            rating=7,
            comments='Initial comments',
            areas_to_improve='Initial areas to improve'
        )

        # Авторизуемся и обновляем
        self.client.force_authenticate(user=self.__class__.employee_user)

        data = {
            'rating': 9,
            'comments': 'Updated comments',
            'areas_to_improve': 'Updated areas to improve'
        }

        url = reverse(
            'goal-self-assessment-detail',
            kwargs={'goal_pk': self.__class__.in_progress_goal.pk, 'pk': self_assessment.pk}
        )
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['rating'], 9)
        
        # Проверяем, что обновление сохранено в БД
        self_assessment.refresh_from_db()
        self.assertEqual(self_assessment.rating, 9)
        self.assertEqual(self_assessment.comments, 'Updated comments')

    def test_self_assessment_get_success(self):
        """Тест успешного получения самооценки"""
        # Создаем самооценку
        self_assessment = SelfAssessment.objects.create(
            goal=self.__class__.in_progress_goal,
            rating=7,
            comments='Test comments',
            areas_to_improve='Test areas to improve'
        )

        # Авторизуемся и получаем
        self.client.force_authenticate(user=self.__class__.employee_user)

        url = reverse(
            'goal-self-assessment-detail',
            kwargs={'goal_pk': self.__class__.in_progress_goal.pk, 'pk': self_assessment.pk}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['rating'], 7)
        self.assertEqual(response.data['comments'], 'Test comments')

    def test_self_assessment_get_by_manager_success(self):
        """Тест получения самооценки руководителем"""
        # Создаем самооценку
        self_assessment = SelfAssessment.objects.create(
            goal=self.__class__.in_progress_goal,
            rating=7,
            comments='Test comments',
            areas_to_improve='Test areas to improve'
        )

        # Авторизуемся руководителем и получаем
        self.client.force_authenticate(user=self.__class__.manager_user)

        url = reverse(
            'goal-self-assessment-detail',
            kwargs={'goal_pk': self.__class__.in_progress_goal.pk, 'pk': self_assessment.pk}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['rating'], 7)

    def test_self_assessment_get_by_other_employee_forbidden(self):
        """Тест запрета получения самооценки другим сотрудником"""
        # Создаем самооценку
        self_assessment = SelfAssessment.objects.create(
            goal=self.__class__.in_progress_goal,
            rating=7,
            comments='Test comments',
            areas_to_improve='Test areas to improve'
        )

        # Авторизуемся другим сотрудником и пытаемся получить
        self.client.force_authenticate(user=self.__class__.employee2_user)

        url = reverse(
            'goal-self-assessment-detail',
            kwargs={'goal_pk': self.__class__.in_progress_goal.pk, 'pk': self_assessment.pk}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_self_assessment_create_for_completed_goal_error(self):
        """Тест ошибки при создании самооценки для завершенной цели"""
        # Создаем завершенную цель
        completed_goal = Goal.objects.create(
            employee=self.__class__.employee,
            title='Completed Goal',
            description='Completed Description',
            expected_results='Completed Expected Results',
            start_period=timezone.now().date(),
            end_period=timezone.now().date() + timedelta(days=30),
            status=Goal.STATUS_COMPLETED
        )

        # Авторизуемся и пытаемся создать самооценку
        self.client.force_authenticate(user=self.__class__.employee_user)

        data = {
            'rating': 8,
            'comments': 'Assessment for completed goal',
            'areas_to_improve': 'Areas for completed goal'
        }

        url = reverse(
            'goal-self-assessment-list',
            kwargs={'goal_pk': completed_goal.pk}
        )
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(SelfAssessment.objects.count(), 0)

    def test_self_assessment_create_duplicate_error(self):
        """Тест ошибки при создании дублирующей самооценки"""
        # Создаем самооценку
        SelfAssessment.objects.create(
            goal=self.__class__.in_progress_goal,
            rating=7,
            comments='Initial comments',
            areas_to_improve='Initial areas to improve'
        )

        # Авторизуемся и пытаемся создать еще одну самооценку
        self.client.force_authenticate(user=self.__class__.employee_user)

        data = {
            'rating': 8,
            'comments': 'Duplicate assessment',
            'areas_to_improve': 'Duplicate areas'
        }

        response = self.client.post(self.in_progress_self_assessment_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(SelfAssessment.objects.count(), 1) 