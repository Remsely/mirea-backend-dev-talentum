from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import User, Employee
from goals.models import Goal
from feedback.models import FeedbackRequest
from feedback.permissions import (
    CanRequestFeedback, CanProvideFeedback, CanProvideExpertEvaluation
)


class FeedbackPermissionsTestCase(APITestCase):
    """Тесты разрешений для модуля отзывов и оценок"""

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

        # Создаем пользователя без профиля сотрудника
        cls.user_without_profile = User.objects.create_user(
            username='regular',
            password='password123',
            email='regular@example.com',
            first_name='Regular',
            last_name='User',
            role='employee'
        )

        # Создаем цели в разных статусах
        cls.draft_goal = Goal.objects.create(
            employee=cls.employee,
            title='Draft Goal',
            description='Draft Description',
            expected_results='Draft Expected Results',
            start_period=today,
            end_period=end_date,
            status=Goal.STATUS_DRAFT
        )

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

    def setUp(self):
        """Подготовка данных перед каждым тестом"""
        # Создаем запрос отзыва
        self.feedback_request = FeedbackRequest.objects.create(
            goal=self.__class__.pending_assessment_goal,
            reviewer=self.__class__.employee2,
            requested_by=self.__class__.employee,
            message='Please review',
            status=FeedbackRequest.STATUS_PENDING
        )

        # Создаем разрешения
        self.can_request_feedback = CanRequestFeedback()
        self.can_provide_feedback = CanProvideFeedback()
        self.can_provide_expert_evaluation = CanProvideExpertEvaluation()

        # Создаем mock request
        self.mock_request = type('MockRequest', (), {'user': None})

    def test_can_request_feedback_permission(self):
        """Тест разрешения на запрос отзыва"""
        # Неаутентифицированный пользователь
        self.mock_request.user = None
        self.assertFalse(self.can_request_feedback.has_permission(self.mock_request, None))
        
        # Пользователь без профиля сотрудника
        self.mock_request.user = self.__class__.user_without_profile
        self.assertFalse(self.can_request_feedback.has_permission(self.mock_request, None))
        
        # Аутентифицированный сотрудник
        self.mock_request.user = self.__class__.employee_user
        self.assertTrue(self.can_request_feedback.has_permission(self.mock_request, None))
        
        # Проверка has_object_permission
        
        # Цель в статусе "Ожидает оценки" и принадлежит сотруднику
        self.assertTrue(self.can_request_feedback.has_object_permission(
            self.mock_request, None, self.__class__.pending_assessment_goal))
        
        # Цель в статусе "Черновик" и принадлежит сотруднику
        self.assertFalse(self.can_request_feedback.has_object_permission(
            self.mock_request, None, self.__class__.draft_goal))
        
        # Цель в статусе "В процессе" и принадлежит сотруднику
        self.assertFalse(self.can_request_feedback.has_object_permission(
            self.mock_request, None, self.__class__.in_progress_goal))
        
        # Цель принадлежит другому сотруднику
        other_goal = Goal.objects.create(
            employee=self.__class__.employee2,
            title='Other Goal',
            description='Other Description',
            expected_results='Other Expected Results',
            start_period=timezone.now().date(),
            end_period=timezone.now().date() + timedelta(days=30),
            status=Goal.STATUS_PENDING_ASSESSMENT
        )
        self.assertFalse(self.can_request_feedback.has_object_permission(
            self.mock_request, None, other_goal))
        
        # Не цель
        self.assertFalse(self.can_request_feedback.has_object_permission(
            self.mock_request, None, object()))

    def test_can_provide_feedback_permission(self):
        """Тест разрешения на предоставление отзыва"""
        # Неаутентифицированный пользователь
        self.mock_request.user = None
        self.assertFalse(self.can_provide_feedback.has_permission(self.mock_request, None))
        
        # Пользователь без профиля сотрудника
        self.mock_request.user = self.__class__.user_without_profile
        self.assertFalse(self.can_provide_feedback.has_permission(self.mock_request, None))
        
        # Аутентифицированный сотрудник
        self.mock_request.user = self.__class__.employee_user
        self.assertTrue(self.can_provide_feedback.has_permission(self.mock_request, None))
        
        # Проверка has_object_permission
        
        # Рецензент = текущий пользователь, статус = ожидает отзыва
        self.mock_request.user = self.__class__.employee2_user
        self.assertTrue(self.can_provide_feedback.has_object_permission(
            self.mock_request, None, self.feedback_request))
        
        # Рецензент != текущий пользователь
        self.mock_request.user = self.__class__.employee_user
        self.assertFalse(self.can_provide_feedback.has_object_permission(
            self.mock_request, None, self.feedback_request))
        
        # Статус != ожидает отзыва
        self.feedback_request.status = FeedbackRequest.STATUS_COMPLETED
        self.feedback_request.save()
        
        self.mock_request.user = self.__class__.employee2_user
        self.assertFalse(self.can_provide_feedback.has_object_permission(
            self.mock_request, None, self.feedback_request))

    def test_can_provide_expert_evaluation_permission(self):
        """Тест разрешения на предоставление экспертной оценки"""
        # Неаутентифицированный пользователь
        self.mock_request.user = None
        self.assertFalse(self.can_provide_expert_evaluation.has_permission(self.mock_request, None))
        
        # Обычный сотрудник
        self.mock_request.user = self.__class__.employee_user
        self.assertFalse(self.can_provide_expert_evaluation.has_permission(self.mock_request, None))
        
        # Менеджер
        self.mock_request.user = self.__class__.manager_user
        self.assertFalse(self.can_provide_expert_evaluation.has_permission(self.mock_request, None))
        
        # Лидер профессии
        self.mock_request.user = self.__class__.expertise_leader_user
        self.assertTrue(self.can_provide_expert_evaluation.has_permission(self.mock_request, None))
        
        # Проверка has_object_permission
        
        # Цель в статусе "Ожидает оценки"
        self.assertTrue(self.can_provide_expert_evaluation.has_object_permission(
            self.mock_request, None, self.__class__.pending_assessment_goal))
        
        # Цель в другом статусе
        self.assertFalse(self.can_provide_expert_evaluation.has_object_permission(
            self.mock_request, None, self.__class__.draft_goal))
        self.assertFalse(self.can_provide_expert_evaluation.has_object_permission(
            self.mock_request, None, self.__class__.in_progress_goal)) 