from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import User, Employee
from goals.models import Goal
from feedback.models import SelfAssessment, FeedbackRequest, PeerFeedback, ExpertEvaluation
from feedback.serializers import (
    SelfAssessmentSerializer, FeedbackRequestListSerializer,
    FeedbackRequestCreateSerializer, PeerFeedbackSerializer,
    ExpertEvaluationSerializer
)


class FeedbackSerializersTestCase(APITestCase):
    """Тесты сериализаторов для модуля отзывов и оценок"""

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

        # Создаем цель
        cls.goal = Goal.objects.create(
            employee=cls.employee,
            title='Test Goal',
            description='Test Description',
            expected_results='Test Expected Results',
            start_period=today,
            end_period=end_date,
            status=Goal.STATUS_PENDING_ASSESSMENT
        )

    def test_self_assessment_serializer(self):
        """Тест сериализатора самооценки"""
        # Создаем самооценку
        self_assessment = SelfAssessment.objects.create(
            goal=self.__class__.goal,
            rating=8,
            comments='Self assessment comments',
            areas_to_improve='Areas to improve'
        )
        
        # Тестируем сериализацию
        serializer = SelfAssessmentSerializer(self_assessment)
        data = serializer.data
        
        self.assertEqual(data['rating'], 8)
        self.assertEqual(data['comments'], 'Self assessment comments')
        self.assertEqual(data['areas_to_improve'], 'Areas to improve')
        self.assertIn('id', data)
        self.assertIn('created_dttm', data)
        
        # Тестируем валидацию и создание
        new_data = {
            'rating': 9,
            'comments': 'New comments',
            'areas_to_improve': 'New areas to improve'
        }
        
        serializer = SelfAssessmentSerializer(data=new_data)
        self.assertTrue(serializer.is_valid())
        
        # Проверяем read_only поля
        read_only_fields = ('id', 'created_dttm')
        for field in read_only_fields:
            self.assertTrue(field in serializer.Meta.read_only_fields)

    def test_feedback_request_list_serializer(self):
        """Тест сериализатора списка запросов отзывов"""
        # Создаем запрос отзыва
        feedback_request = FeedbackRequest.objects.create(
            goal=self.__class__.goal,
            reviewer=self.__class__.employee2,
            requested_by=self.__class__.employee,
            message='Please review'
        )
        
        # Тестируем сериализацию
        serializer = FeedbackRequestListSerializer(feedback_request)
        data = serializer.data
        
        self.assertEqual(data['message'], 'Please review')
        self.assertEqual(data['status'], FeedbackRequest.STATUS_PENDING)
        self.assertEqual(data['status_display'], 'Ожидает отзыва')
        self.assertEqual(data['reviewer']['id'], self.__class__.employee2.id)
        self.assertEqual(data['requested_by']['id'], self.__class__.employee.id)
        self.assertEqual(data['goal'], self.__class__.goal.id)
        
        # Проверяем read_only поля
        read_only_fields = ('id', 'goal', 'status', 'status_display', 'created_dttm')
        for field in read_only_fields:
            self.assertTrue(field in serializer.Meta.read_only_fields)

    def test_feedback_request_create_serializer(self):
        """Тест сериализатора создания запроса отзыва"""
        # Данные для создания
        data = {
            'reviewer': self.__class__.employee2.id,
            'message': 'Please review my goal'
        }
        
        # Создаем контекст
        mock_request = type('MockRequest', (), {'user': self.__class__.employee_user})
        context = {
            'request': mock_request,
            'goal_id': self.__class__.goal.id
        }
        
        # Тестируем валидацию
        serializer = FeedbackRequestCreateSerializer(data=data, context=context)
        self.assertTrue(serializer.is_valid())
        
        # Тестируем create
        feedback_request = serializer.save()
        
        self.assertEqual(feedback_request.goal.id, self.__class__.goal.id)
        self.assertEqual(feedback_request.reviewer.id, self.__class__.employee2.id)
        self.assertEqual(feedback_request.requested_by.id, self.__class__.employee.id)
        self.assertEqual(feedback_request.message, 'Please review my goal')
        
        # Тестируем валидацию запроса отзыва самому себе
        data_self_review = {
            'reviewer': self.__class__.employee.id,
            'message': 'Self review'
        }
        serializer = FeedbackRequestCreateSerializer(data=data_self_review, context=context)
        self.assertFalse(serializer.is_valid())
        self.assertIn('reviewer', serializer.errors)
        
        # Тестируем валидацию дублирующего запроса
        data_duplicate = {
            'reviewer': self.__class__.employee2.id,
            'message': 'Duplicate review'
        }
        serializer = FeedbackRequestCreateSerializer(data=data_duplicate, context=context)
        self.assertFalse(serializer.is_valid())
        self.assertIn('reviewer', serializer.errors)

    def test_peer_feedback_serializer(self):
        """Тест сериализатора отзыва коллеги"""
        # Создаем запрос отзыва
        feedback_request = FeedbackRequest.objects.create(
            goal=self.__class__.goal,
            reviewer=self.__class__.employee2,
            requested_by=self.__class__.employee,
            message='Please review'
        )
        
        # Создаем отзыв коллеги
        peer_feedback = PeerFeedback.objects.create(
            feedback_request=feedback_request,
            rating=7,
            comments='Peer feedback comments',
            areas_to_improve='Areas to improve'
        )
        
        # Тестируем сериализацию
        serializer = PeerFeedbackSerializer(peer_feedback)
        data = serializer.data
        
        self.assertEqual(data['rating'], 7)
        self.assertEqual(data['comments'], 'Peer feedback comments')
        self.assertEqual(data['areas_to_improve'], 'Areas to improve')
        self.assertEqual(data['reviewer']['id'], self.__class__.employee2.id)
        self.assertEqual(data['goal']['id'], self.__class__.goal.id)
        self.assertEqual(data['goal']['title'], self.__class__.goal.title)
        
        # Тестируем валидацию и создание
        new_data = {
            'rating': 9,
            'comments': 'New feedback comments',
            'areas_to_improve': 'New areas to improve'
        }
        
        serializer = PeerFeedbackSerializer(data=new_data)
        self.assertTrue(serializer.is_valid())
        
        # Проверяем read_only поля
        read_only_fields = ('id', 'reviewer', 'goal', 'created_dttm')
        for field in read_only_fields:
            self.assertTrue(field in serializer.Meta.read_only_fields)

    def test_expert_evaluation_serializer(self):
        """Тест сериализатора экспертной оценки"""
        # Создаем экспертную оценку
        expert_evaluation = ExpertEvaluation.objects.create(
            goal=self.__class__.goal,
            expert=self.__class__.expertise_leader,
            final_rating=9,
            comments='Expert evaluation comments',
            areas_to_improve='Expert areas to improve'
        )
        
        # Тестируем сериализацию
        serializer = ExpertEvaluationSerializer(expert_evaluation)
        data = serializer.data
        
        self.assertEqual(data['final_rating'], 9)
        self.assertEqual(data['comments'], 'Expert evaluation comments')
        self.assertEqual(data['areas_to_improve'], 'Expert areas to improve')
        self.assertEqual(data['expert']['id'], self.__class__.expertise_leader.id)
        
        # Тестируем валидацию и создание
        new_data = {
            'final_rating': 8,
            'comments': 'New expert comments',
            'areas_to_improve': 'New expert areas to improve'
        }
        
        # Создаем контекст
        mock_request = type('MockRequest', (), {'user': self.__class__.expertise_leader_user})
        context = {
            'request': mock_request,
            'goal_id': self.__class__.goal.id
        }
        
        serializer = ExpertEvaluationSerializer(data=new_data, context=context)
        self.assertTrue(serializer.is_valid())
        
        # Проверяем read_only поля
        read_only_fields = ('id', 'expert', 'created_dttm')
        for field in read_only_fields:
            self.assertTrue(field in serializer.Meta.read_only_fields) 