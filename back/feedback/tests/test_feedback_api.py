from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User, Employee
from goals.models import Goal
from feedback.models import SelfAssessment, FeedbackRequest, PeerFeedback, ExpertEvaluation


class FeedbackModelsTestCase(APITestCase):
    """Тесты моделей отзывов и оценок"""

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

        # Создаем другого сотрудника (коллегу)
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

        # Создаем третьего сотрудника
        cls.employee3_user = User.objects.create_user(
            username='employee3',
            password='password123',
            email='employee3@example.com',
            first_name='Employee3',
            last_name='User',
            role='employee'
        )
        cls.employee3 = Employee.objects.create(
            user=cls.employee3_user,
            position='QA Engineer',
            hire_dt=today,
            manager=cls.manager
        )

        # Общие данные для цели
        cls.goal_data = {
            'title': 'Test Goal',
            'description': 'Test Description',
            'expected_results': 'Test Expected Results',
            'start_period': today,
            'end_period': end_date,
        }

    def setUp(self):
        """Создание и настройка цели перед каждым тестом"""
        # Создаем цель в статусе "Ожидает оценки"
        self.goal = Goal.objects.create(
            employee=self.__class__.employee,
            status=Goal.STATUS_PENDING_ASSESSMENT,
            **self.__class__.goal_data
        )

    def test_self_assessment_create(self):
        """Тест создания самооценки"""
        # Создаем самооценку
        self_assessment = SelfAssessment.objects.create(
            goal=self.goal,
            rating=8,
            comments='Self assessment comments',
            areas_to_improve='Areas to improve'
        )
        
        self.assertEqual(self_assessment.rating, 8)
        self.assertEqual(self_assessment.goal, self.goal)
        self.assertEqual(SelfAssessment.objects.count(), 1)
        
        # Проверяем строковое представление
        expected_str = f"Самооценка для {self.goal.title}"
        self.assertEqual(str(self_assessment), expected_str)

    def test_feedback_request_create(self):
        """Тест создания запроса отзыва"""
        # Создаем запрос отзыва
        feedback_request = FeedbackRequest.objects.create(
            goal=self.goal,
            reviewer=self.__class__.employee2,
            requested_by=self.__class__.employee,
            message='Please provide feedback on my goal'
        )
        
        self.assertEqual(feedback_request.status, FeedbackRequest.STATUS_PENDING)
        self.assertEqual(feedback_request.reviewer, self.__class__.employee2)
        self.assertEqual(feedback_request.requested_by, self.__class__.employee)
        self.assertEqual(FeedbackRequest.objects.count(), 1)
        
        # Проверяем строковое представление
        expected_str = f"Запрос отзыва от {self.__class__.employee.user.get_full_name()} для {self.__class__.employee2.user.get_full_name()}"
        self.assertEqual(str(feedback_request), expected_str)

    def test_peer_feedback_create(self):
        """Тест создания отзыва коллеги"""
        # Создаем запрос отзыва
        feedback_request = FeedbackRequest.objects.create(
            goal=self.goal,
            reviewer=self.__class__.employee2,
            requested_by=self.__class__.employee,
            message='Please provide feedback on my goal'
        )
        
        # Создаем отзыв коллеги
        peer_feedback = PeerFeedback.objects.create(
            feedback_request=feedback_request,
            rating=7,
            comments='Peer feedback comments',
            areas_to_improve='Peer feedback areas to improve'
        )
        
        self.assertEqual(peer_feedback.rating, 7)
        self.assertEqual(peer_feedback.feedback_request, feedback_request)
        self.assertEqual(PeerFeedback.objects.count(), 1)
        
        # Проверяем, что статус запроса изменился на "завершен"
        feedback_request.refresh_from_db()
        self.assertEqual(feedback_request.status, FeedbackRequest.STATUS_COMPLETED)
        
        # Проверяем строковое представление
        expected_str = f"Отзыв от {self.__class__.employee2.user.get_full_name()} на цель {self.goal.title}"
        self.assertEqual(str(peer_feedback), expected_str)

    def test_expert_evaluation_create(self):
        """Тест создания экспертной оценки"""
        # Создаем самооценку
        self_assessment = SelfAssessment.objects.create(
            goal=self.goal,
            rating=8,
            comments='Self assessment comments',
            areas_to_improve='Areas to improve'
        )
        
        # Создаем запрос отзыва и отзыв коллеги
        feedback_request = FeedbackRequest.objects.create(
            goal=self.goal,
            reviewer=self.__class__.employee2,
            requested_by=self.__class__.employee,
            status=FeedbackRequest.STATUS_COMPLETED
        )
        
        peer_feedback = PeerFeedback.objects.create(
            feedback_request=feedback_request,
            rating=7,
            comments='Peer feedback comments',
            areas_to_improve='Peer feedback areas to improve'
        )
        
        # Создаем экспертную оценку
        expert_evaluation = ExpertEvaluation.objects.create(
            goal=self.goal,
            expert=self.__class__.expertise_leader,
            final_rating=9,
            comments='Expert evaluation comments',
            areas_to_improve='Expert evaluation areas to improve'
        )
        
        self.assertEqual(expert_evaluation.final_rating, 9)
        self.assertEqual(expert_evaluation.expert, self.__class__.expertise_leader)
        self.assertEqual(ExpertEvaluation.objects.count(), 1)
        
        # Проверяем, что цель переведена в статус "Завершено"
        self.goal.refresh_from_db()
        self.assertEqual(self.goal.status, Goal.STATUS_COMPLETED)
        
        # Проверяем строковое представление
        expected_str = f"Оценка от {self.__class__.expertise_leader.user.get_full_name()} на цель {self.goal.title}"
        self.assertEqual(str(expert_evaluation), expected_str)

    def test_multiple_feedback_requests(self):
        """Тест создания нескольких запросов отзывов"""
        # Создаем запросы отзывов от нескольких рецензентов
        feedback_request1 = FeedbackRequest.objects.create(
            goal=self.goal,
            reviewer=self.__class__.employee2,
            requested_by=self.__class__.employee,
            message='Feedback request 1'
        )
        
        feedback_request2 = FeedbackRequest.objects.create(
            goal=self.goal,
            reviewer=self.__class__.employee3,
            requested_by=self.__class__.employee,
            message='Feedback request 2'
        )
        
        self.assertEqual(FeedbackRequest.objects.count(), 2)
        self.assertEqual(FeedbackRequest.objects.filter(goal=self.goal).count(), 2)
        
        # Проверяем, что нельзя создать дублирующий запрос от того же рецензента
        with self.assertRaises(Exception):
            FeedbackRequest.objects.create(
                goal=self.goal,
                reviewer=self.__class__.employee2,
                requested_by=self.__class__.employee,
                message='Duplicate feedback request'
            ) 
