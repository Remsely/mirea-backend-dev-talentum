from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User, Employee
from goals.models import Goal
from feedback.models import FeedbackRequest, PeerFeedback


class FeedbackRequestsAPITestCase(APITestCase):
    """Тесты API для запросов отзывов"""

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

        # Создаем цель для другого сотрудника
        cls.other_goal = Goal.objects.create(
            employee=cls.employee2,
            title='Other Goal',
            description='Other Description',
            expected_results='Other Expected Results',
            start_period=today,
            end_period=end_date,
            status=Goal.STATUS_PENDING_ASSESSMENT
        )

    def setUp(self):
        """Настройка перед каждым тестом"""
        # URL-адреса для тестов
        self.feedback_requests_url = reverse(
            'goal-feedback-request-list',
            kwargs={'goal_pk': self.__class__.goal.pk}
        )
        self.other_feedback_requests_url = reverse(
            'goal-feedback-request-list',
            kwargs={'goal_pk': self.__class__.other_goal.pk}
        )
        self.my_feedback_requests_url = reverse(
            'my-feedback-requests-list',
            kwargs={'goal_pk': self.__class__.goal.pk}
        )

    def test_feedback_request_create_success(self):
        """Тест успешного создания запроса отзыва"""
        self.client.force_authenticate(user=self.__class__.employee_user)

        data = {
            'reviewer': self.__class__.employee2.id,
            'message': 'Please provide feedback on my goal'
        }

        response = self.client.post(self.feedback_requests_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FeedbackRequest.objects.count(), 1)

        created_request = FeedbackRequest.objects.first()
        self.assertEqual(created_request.goal, self.__class__.goal)
        self.assertEqual(created_request.reviewer, self.__class__.employee2)
        self.assertEqual(created_request.requested_by, self.__class__.employee)
        self.assertEqual(created_request.message, 'Please provide feedback on my goal')
        self.assertEqual(created_request.status, FeedbackRequest.STATUS_PENDING)

    def test_feedback_request_create_by_other_user_forbidden(self):
        """Тест запрета создания запроса отзыва другим пользователем"""
        self.client.force_authenticate(user=self.__class__.employee2_user)

        data = {
            'reviewer': self.__class__.employee3.id,
            'message': 'Unauthorized request'
        }

        response = self.client.post(self.feedback_requests_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(FeedbackRequest.objects.count(), 0)

    def test_feedback_request_create_to_self_error(self):
        """Тест ошибки при создании запроса отзыва самому себе"""
        self.client.force_authenticate(user=self.__class__.employee_user)

        data = {
            'reviewer': self.__class__.employee.id,
            'message': 'Self-review request'
        }

        response = self.client.post(self.feedback_requests_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(FeedbackRequest.objects.count(), 0)

    def test_feedback_request_create_multiple_reviewers(self):
        """Тест создания запросов отзывов от нескольких рецензентов"""
        self.client.force_authenticate(user=self.__class__.employee_user)

        # Создаем запрос первому рецензенту
        data1 = {
            'reviewer': self.__class__.employee2.id,
            'message': 'Please provide feedback - reviewer 1'
        }
        response1 = self.client.post(self.feedback_requests_url, data1)
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Создаем запрос второму рецензенту
        data2 = {
            'reviewer': self.__class__.employee3.id,
            'message': 'Please provide feedback - reviewer 2'
        }
        response2 = self.client.post(self.feedback_requests_url, data2)
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)

        # Проверяем, что оба запроса созданы
        self.assertEqual(FeedbackRequest.objects.count(), 2)
        
        # Проверяем список запросов отзывов для цели
        response = self.client.get(self.feedback_requests_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_my_feedback_requests_list(self):
        """Тест получения списка запросов отзывов, адресованных текущему пользователю"""
        # Создаем запрос отзыва
        feedback_request = FeedbackRequest.objects.create(
            goal=self.__class__.goal,
            reviewer=self.__class__.employee2,
            requested_by=self.__class__.employee,
            message='Please provide feedback'
        )

        # Авторизуемся как рецензент и получаем список запросов
        self.client.force_authenticate(user=self.__class__.employee2_user)
        response = self.client.get(self.my_feedback_requests_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], feedback_request.id)
        self.assertEqual(response.data[0]['message'], 'Please provide feedback')

    def test_feedback_request_list_by_goal_owner(self):
        """Тест получения списка запросов отзывов владельцем цели"""
        # Создаем запросы отзывов
        FeedbackRequest.objects.create(
            goal=self.__class__.goal,
            reviewer=self.__class__.employee2,
            requested_by=self.__class__.employee,
            message='First feedback request'
        )
        FeedbackRequest.objects.create(
            goal=self.__class__.goal,
            reviewer=self.__class__.employee3,
            requested_by=self.__class__.employee,
            message='Second feedback request'
        )

        # Авторизуемся как владелец цели и получаем список запросов
        self.client.force_authenticate(user=self.__class__.employee_user)
        response = self.client.get(self.feedback_requests_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_feedback_request_list_by_manager(self):
        """Тест получения списка запросов отзывов руководителем"""
        # Создаем запросы отзывов
        FeedbackRequest.objects.create(
            goal=self.__class__.goal,
            reviewer=self.__class__.employee2,
            requested_by=self.__class__.employee,
            message='Feedback request'
        )

        # Авторизуемся как руководитель и получаем список запросов
        self.client.force_authenticate(user=self.__class__.manager_user)
        response = self.client.get(self.feedback_requests_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_feedback_request_list_by_other_employee_forbidden(self):
        """Тест запрета получения списка запросов отзывов другим сотрудником"""
        # Создаем запросы отзывов
        FeedbackRequest.objects.create(
            goal=self.__class__.goal,
            reviewer=self.__class__.employee2,
            requested_by=self.__class__.employee,
            message='Feedback request'
        )

        # Авторизуемся как сотрудник, не связанный с целью или запросом
        self.client.force_authenticate(user=self.__class__.employee3_user)
        response = self.client.get(self.feedback_requests_url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_peer_feedback_create_success(self):
        """Тест успешного создания отзыва на запрос отзыва"""
        # Создаем запрос отзыва
        feedback_request = FeedbackRequest.objects.create(
            goal=self.__class__.goal,
            reviewer=self.__class__.employee2,
            requested_by=self.__class__.employee,
            message='Please provide feedback'
        )

        # Формируем URL для создания отзыва
        peer_feedback_url = reverse(
            'feedback-request-feedback-list',
            kwargs={
                'goal_pk': self.__class__.goal.pk,
                'request_pk': feedback_request.pk
            }
        )

        # Авторизуемся как рецензент и создаем отзыв
        self.client.force_authenticate(user=self.__class__.employee2_user)
        
        data = {
            'rating': 8,
            'comments': 'Good job on the goal implementation',
            'areas_to_improve': 'Could improve documentation'
        }

        response = self.client.post(peer_feedback_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PeerFeedback.objects.count(), 1)
        
        # Проверяем, что статус запроса изменился на "завершен"
        feedback_request.refresh_from_db()
        self.assertEqual(feedback_request.status, FeedbackRequest.STATUS_COMPLETED)

    def test_peer_feedback_by_wrong_user_forbidden(self):
        """Тест запрета создания отзыва пользователем, не являющимся рецензентом"""
        # Создаем запрос отзыва
        feedback_request = FeedbackRequest.objects.create(
            goal=self.__class__.goal,
            reviewer=self.__class__.employee2,
            requested_by=self.__class__.employee,
            message='Please provide feedback'
        )

        # Формируем URL для создания отзыва
        peer_feedback_url = reverse(
            'feedback-request-feedback-list',
            kwargs={
                'goal_pk': self.__class__.goal.pk,
                'request_pk': feedback_request.pk
            }
        )

        # Авторизуемся как пользователь, не являющийся рецензентом, и пытаемся создать отзыв
        self.client.force_authenticate(user=self.__class__.employee3_user)
        
        data = {
            'rating': 6,
            'comments': 'Unauthorized feedback',
            'areas_to_improve': 'This should not work'
        }

        response = self.client.post(peer_feedback_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(PeerFeedback.objects.count(), 0) 