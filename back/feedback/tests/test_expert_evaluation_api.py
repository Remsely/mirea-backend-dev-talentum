from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User, Employee
from goals.models import Goal
from feedback.models import SelfAssessment, FeedbackRequest, PeerFeedback, ExpertEvaluation


class ExpertEvaluationAPITestCase(APITestCase):
    """Тесты API для экспертной оценки"""

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

        # Создаем цель в статусе "Ожидает оценки"
        cls.goal = Goal.objects.create(
            employee=cls.employee,
            title='Test Goal',
            description='Test Description',
            expected_results='Test Expected Results',
            start_period=today,
            end_period=end_date,
            status=Goal.STATUS_PENDING_ASSESSMENT
        )

        # Создаем цель в другом статусе
        cls.in_progress_goal = Goal.objects.create(
            employee=cls.employee,
            title='In Progress Goal',
            description='In Progress Description',
            expected_results='In Progress Expected Results',
            start_period=today,
            end_period=end_date,
            status=Goal.STATUS_IN_PROGRESS
        )

    def setUp(self):
        """Настройка перед каждым тестом"""
        # Создаем самооценку и отзыв коллеги для цели
        self.self_assessment = SelfAssessment.objects.create(
            goal=self.__class__.goal,
            rating=8,
            comments='Self assessment comments',
            areas_to_improve='Self assessment areas to improve'
        )
        
        self.feedback_request = FeedbackRequest.objects.create(
            goal=self.__class__.goal,
            reviewer=self.__class__.employee2,
            requested_by=self.__class__.employee,
            message='Please review my goal',
            status=FeedbackRequest.STATUS_COMPLETED
        )
        
        self.peer_feedback = PeerFeedback.objects.create(
            feedback_request=self.feedback_request,
            rating=7,
            comments='Peer feedback comments',
            areas_to_improve='Peer feedback areas to improve'
        )

        # URL для экспертной оценки
        self.expert_evaluation_url = reverse(
            'goal-expert-evaluation-list',
            kwargs={'goal_pk': self.__class__.goal.pk}
        )
        
        self.in_progress_expert_evaluation_url = reverse(
            'goal-expert-evaluation-list',
            kwargs={'goal_pk': self.__class__.in_progress_goal.pk}
        )

    def test_expert_evaluation_create_success(self):
        """Тест успешного создания экспертной оценки"""
        self.client.force_authenticate(user=self.__class__.expertise_leader_user)

        data = {
            'final_rating': 8,
            'comments': 'Final evaluation comments',
            'areas_to_improve': 'Final areas to improve'
        }

        response = self.client.post(self.expert_evaluation_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ExpertEvaluation.objects.count(), 1)
        
        # Проверяем, что цель переведена в статус "Завершено"
        self.__class__.goal.refresh_from_db()
        self.assertEqual(self.__class__.goal.status, Goal.STATUS_COMPLETED)
        
        # Проверяем поля созданной оценки
        expert_evaluation = ExpertEvaluation.objects.first()
        self.assertEqual(expert_evaluation.goal, self.__class__.goal)
        self.assertEqual(expert_evaluation.expert, self.__class__.expertise_leader)
        self.assertEqual(expert_evaluation.final_rating, 8)
        self.assertEqual(expert_evaluation.comments, 'Final evaluation comments')

    def test_expert_evaluation_by_non_leader_forbidden(self):
        """Тест запрета создания экспертной оценки не лидером профессии"""
        # Обычный сотрудник
        self.client.force_authenticate(user=self.__class__.employee_user)

        data = {
            'final_rating': 7,
            'comments': 'Employee evaluation',
            'areas_to_improve': 'Employee areas'
        }

        response = self.client.post(self.expert_evaluation_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(ExpertEvaluation.objects.count(), 0)
        
        # Менеджер
        self.client.force_authenticate(user=self.__class__.manager_user)
        response = self.client.post(self.expert_evaluation_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(ExpertEvaluation.objects.count(), 0)

    def test_expert_evaluation_wrong_goal_status(self):
        """Тест ошибки при создании экспертной оценки для цели в неподходящем статусе"""
        self.client.force_authenticate(user=self.__class__.expertise_leader_user)

        data = {
            'final_rating': 8,
            'comments': 'Final evaluation comments',
            'areas_to_improve': 'Final areas to improve'
        }

        response = self.client.post(self.in_progress_expert_evaluation_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(ExpertEvaluation.objects.count(), 0)

    def test_expert_evaluation_without_self_assessment(self):
        """Тест ошибки при создании экспертной оценки без самооценки"""
        # Удаляем самооценку
        self.self_assessment.delete()
        
        self.client.force_authenticate(user=self.__class__.expertise_leader_user)

        data = {
            'final_rating': 8,
            'comments': 'Final evaluation comments',
            'areas_to_improve': 'Final areas to improve'
        }

        response = self.client.post(self.expert_evaluation_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ExpertEvaluation.objects.count(), 0)

    def test_expert_evaluation_without_peer_feedback(self):
        """Тест ошибки при создании экспертной оценки без отзывов коллег"""
        # Удаляем отзыв коллеги
        self.peer_feedback.delete()
        
        self.client.force_authenticate(user=self.__class__.expertise_leader_user)

        data = {
            'final_rating': 8,
            'comments': 'Final evaluation comments',
            'areas_to_improve': 'Final areas to improve'
        }

        response = self.client.post(self.expert_evaluation_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ExpertEvaluation.objects.count(), 0)

    def test_expert_evaluation_get_success(self):
        """Тест успешного получения экспертной оценки"""
        # Создаем экспертную оценку
        expert_evaluation = ExpertEvaluation.objects.create(
            goal=self.__class__.goal,
            expert=self.__class__.expertise_leader,
            final_rating=9,
            comments='Expert evaluation comments',
            areas_to_improve='Expert areas to improve'
        )
        
        # Авторизуемся и получаем оценку
        self.client.force_authenticate(user=self.__class__.employee_user)
        
        url = reverse(
            'goal-expert-evaluation-detail',
            kwargs={'goal_pk': self.__class__.goal.pk, 'pk': expert_evaluation.pk}
        )
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['final_rating'], 9)
        self.assertEqual(response.data['comments'], 'Expert evaluation comments')
        self.assertEqual(response.data['expert']['id'], self.__class__.expertise_leader.id)

    def test_expert_evaluation_create_duplicate_error(self):
        """Тест ошибки при создании дублирующей экспертной оценки"""
        # Создаем экспертную оценку
        ExpertEvaluation.objects.create(
            goal=self.__class__.goal,
            expert=self.__class__.expertise_leader,
            final_rating=9,
            comments='Expert evaluation comments',
            areas_to_improve='Expert areas to improve'
        )
        
        # Авторизуемся и пытаемся создать еще одну оценку
        self.client.force_authenticate(user=self.__class__.expertise_leader_user)

        data = {
            'final_rating': 8,
            'comments': 'Duplicate evaluation',
            'areas_to_improve': 'Duplicate areas'
        }

        response = self.client.post(self.expert_evaluation_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(ExpertEvaluation.objects.count(), 1) 