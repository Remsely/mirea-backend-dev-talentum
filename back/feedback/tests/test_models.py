from datetime import timedelta

from django.utils import timezone
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

    def test_self_assessment_model(self):
        """Тест модели самооценки"""
        # Создаем самооценку
        self_assessment = SelfAssessment.objects.create(
            goal=self.goal,
            rating=8,
            comments='Self assessment comments',
            areas_to_improve='Areas to improve'
        )
        
        # Проверяем поля модели
        self.assertEqual(self_assessment.rating, 8)
        self.assertEqual(self_assessment.goal, self.goal)
        self.assertEqual(self_assessment.comments, 'Self assessment comments')
        self.assertEqual(self_assessment.areas_to_improve, 'Areas to improve')
        
        # Проверяем строковое представление
        expected_str = f"Самооценка для {self.goal.title}"
        self.assertEqual(str(self_assessment), expected_str)
        
        # Проверяем метаданные модели
        self.assertEqual(SelfAssessment._meta.verbose_name, 'Самооценка')
        self.assertEqual(SelfAssessment._meta.verbose_name_plural, 'Самооценки')
        self.assertEqual(SelfAssessment._meta.db_table, 'goals_self_assessments')

    def test_feedback_request_model(self):
        """Тест модели запроса отзыва"""
        # Создаем запрос отзыва
        feedback_request = FeedbackRequest.objects.create(
            goal=self.goal,
            reviewer=self.__class__.employee2,
            requested_by=self.__class__.employee,
            message='Please provide feedback on my goal'
        )
        
        # Проверяем поля модели
        self.assertEqual(feedback_request.goal, self.goal)
        self.assertEqual(feedback_request.reviewer, self.__class__.employee2)
        self.assertEqual(feedback_request.requested_by, self.__class__.employee)
        self.assertEqual(feedback_request.message, 'Please provide feedback on my goal')
        self.assertEqual(feedback_request.status, FeedbackRequest.STATUS_PENDING)
        
        # Проверяем строковое представление
        expected_str = f"Запрос отзыва от {self.__class__.employee.user.get_full_name()} для {self.__class__.employee2.user.get_full_name()}"
        self.assertEqual(str(feedback_request), expected_str)
        
        # Проверяем метаданные модели
        self.assertEqual(FeedbackRequest._meta.verbose_name, 'Запрос отзыва')
        self.assertEqual(FeedbackRequest._meta.verbose_name_plural, 'Запросы отзывов')
        self.assertEqual(FeedbackRequest._meta.db_table, 'feedback_requests')
        
        # Проверяем уникальность пары goal-reviewer
        with self.assertRaises(Exception):
            FeedbackRequest.objects.create(
                goal=self.goal,
                reviewer=self.__class__.employee2,
                requested_by=self.__class__.employee,
                message='Duplicate request'
            )

    def test_peer_feedback_model(self):
        """Тест модели отзыва коллеги"""
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
        
        # Проверяем поля модели
        self.assertEqual(peer_feedback.feedback_request, feedback_request)
        self.assertEqual(peer_feedback.rating, 7)
        self.assertEqual(peer_feedback.comments, 'Peer feedback comments')
        self.assertEqual(peer_feedback.areas_to_improve, 'Peer feedback areas to improve')
        
        # Проверяем строковое представление
        expected_str = f"Отзыв от {self.__class__.employee2.user.get_full_name()} на цель {self.goal.title}"
        self.assertEqual(str(peer_feedback), expected_str)
        
        # Проверяем метаданные модели
        self.assertEqual(PeerFeedback._meta.verbose_name, 'Отзыв коллеги')
        self.assertEqual(PeerFeedback._meta.verbose_name_plural, 'Отзывы коллег')
        self.assertEqual(PeerFeedback._meta.db_table, 'peer_feedback')
        
        # Проверяем, что статус запроса изменился на "завершен"
        feedback_request.refresh_from_db()
        self.assertEqual(feedback_request.status, FeedbackRequest.STATUS_COMPLETED)

    def test_expert_evaluation_model(self):
        """Тест модели экспертной оценки"""
        # Создаем экспертную оценку
        expert_evaluation = ExpertEvaluation.objects.create(
            goal=self.goal,
            expert=self.__class__.expertise_leader,
            final_rating=9,
            comments='Expert evaluation comments',
            areas_to_improve='Expert evaluation areas to improve'
        )
        
        # Проверяем поля модели
        self.assertEqual(expert_evaluation.goal, self.goal)
        self.assertEqual(expert_evaluation.expert, self.__class__.expertise_leader)
        self.assertEqual(expert_evaluation.final_rating, 9)
        self.assertEqual(expert_evaluation.comments, 'Expert evaluation comments')
        self.assertEqual(expert_evaluation.areas_to_improve, 'Expert evaluation areas to improve')
        
        # Проверяем строковое представление
        expected_str = f"Оценка от {self.__class__.expertise_leader.user.get_full_name()} на цель {self.goal.title}"
        self.assertEqual(str(expert_evaluation), expected_str)
        
        # Проверяем метаданные модели
        self.assertEqual(ExpertEvaluation._meta.verbose_name, 'Итоговая оценка от лидера профессии')
        self.assertEqual(ExpertEvaluation._meta.verbose_name_plural, 'Итоговые оценки от лидеров профессии')
        self.assertEqual(ExpertEvaluation._meta.db_table, 'expert_evaluations')
        
        # Проверяем, что цель переведена в статус "Завершено"
        self.goal.refresh_from_db()
        self.assertEqual(self.goal.status, Goal.STATUS_COMPLETED)

    def test_expert_evaluation_save_goal_completion(self):
        """Тест автоматического завершения цели при сохранении экспертной оценки"""
        # Создаем цель в статусе "В процессе"
        in_progress_goal = Goal.objects.create(
            employee=self.__class__.employee,
            status=Goal.STATUS_IN_PROGRESS,
            **self.__class__.goal_data
        )
        
        # Создаем экспертную оценку
        expert_evaluation = ExpertEvaluation.objects.create(
            goal=in_progress_goal,
            expert=self.__class__.expertise_leader,
            final_rating=8,
            comments='Expert evaluation for in progress goal',
            areas_to_improve='Areas to improve for in progress goal'
        )
        
        # Проверяем, что статус цели изменился на "Завершено"
        in_progress_goal.refresh_from_db()
        self.assertEqual(in_progress_goal.status, Goal.STATUS_COMPLETED)

    def test_peer_feedback_save_request_completion(self):
        """Тест автоматического завершения запроса при сохранении отзыва"""
        # Создаем запрос отзыва
        feedback_request = FeedbackRequest.objects.create(
            goal=self.goal,
            reviewer=self.__class__.employee2,
            requested_by=self.__class__.employee,
            message='Request to test completion',
            status=FeedbackRequest.STATUS_PENDING
        )
        
        # Проверяем исходный статус
        self.assertEqual(feedback_request.status, FeedbackRequest.STATUS_PENDING)
        
        # Создаем отзыв коллеги
        peer_feedback = PeerFeedback.objects.create(
            feedback_request=feedback_request,
            rating=6,
            comments='Feedback to test request completion',
            areas_to_improve='Areas to test request completion'
        )
        
        # Проверяем, что статус запроса изменился на "завершен"
        feedback_request.refresh_from_db()
        self.assertEqual(feedback_request.status, FeedbackRequest.STATUS_COMPLETED) 