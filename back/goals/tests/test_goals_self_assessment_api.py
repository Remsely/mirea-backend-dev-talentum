from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User, Employee
from goals.models import Goal, SelfAssessment


class SelfAssessmentAPITestCase(APITestCase):
    """Тесты API для работы с самооценкой"""

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

        # Создаем другого сотрудника
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

        # Базовые данные для целей
        cls.goal_data = {
            'employee': cls.employee,
            'title': 'Test Goal',
            'description': 'Test Description',
            'expected_results': 'Test Expected Results',
            'start_period': today,
            'end_period': end_date,
        }

        # Данные для самооценки
        cls.assessment_data = {
            'rating': 8,
            'comments': 'Self Assessment Comments',
            'areas_to_improve': 'Areas to Improve'
        }

    def setUp(self):
        """Подготовка данных перед каждым тестом"""
        # Создаем цели в разных статусах
        self.goal = Goal.objects.create(
            employee=self.__class__.employee,
            title=self.__class__.goal_data['title'],
            description=self.__class__.goal_data['description'],
            expected_results=self.__class__.goal_data['expected_results'],
            start_period=self.__class__.goal_data['start_period'],
            end_period=self.__class__.goal_data['end_period'],
            status=Goal.STATUS_IN_PROGRESS
        )

        self.pending_goal = Goal.objects.create(
            employee=self.__class__.employee,
            title='Pending Goal',
            description='Pending Description',
            expected_results='Pending Expected Results',
            start_period=self.__class__.goal_data['start_period'],
            end_period=self.__class__.goal_data['end_period'],
            status=Goal.STATUS_PENDING_ASSESSMENT
        )

        self.draft_goal = Goal.objects.create(
            employee=self.__class__.employee,
            title='Draft Goal',
            description='Draft Description',
            expected_results='Draft Expected Results',
            start_period=self.__class__.goal_data['start_period'],
            end_period=self.__class__.goal_data['end_period'],
            status=Goal.STATUS_DRAFT
        )

        # URL-адреса для тестов
        self.assessment_url = reverse('goal-self-assessment-list',
                                      kwargs={'goal_pk': self.goal.pk})
        self.pending_assessment_url = reverse('goal-self-assessment-list',
                                              kwargs={
                                                  'goal_pk': self.pending_goal.pk})
        self.draft_assessment_url = reverse('goal-self-assessment-list',
                                            kwargs={
                                                'goal_pk': self.draft_goal.pk})

    def test_self_assessment_create_success(self):
        """Тест успешного создания самооценки"""
        self.client.force_authenticate(user=self.__class__.employee_user)

        response = self.client.post(self.assessment_url,
                                    self.__class__.assessment_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Проверяем, что самооценка создана
        self.assertEqual(SelfAssessment.objects.count(), 1)
        assessment = SelfAssessment.objects.first()
        self.assertEqual(assessment.rating, 8)
        self.assertEqual(assessment.goal, self.goal)

    def test_self_assessment_create_for_pending_assessment_goal(self):
        """Тест создания самооценки для цели в статусе 'Ожидает оценки'"""
        self.client.force_authenticate(user=self.__class__.employee_user)

        data = {
            'rating': 9,
            'comments': 'Pending Goal Assessment',
            'areas_to_improve': 'More Areas to Improve'
        }

        response = self.client.post(self.pending_assessment_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Проверяем, что самооценка создана
        assessment = SelfAssessment.objects.get(goal=self.pending_goal)
        self.assertEqual(assessment.rating, 9)

    def test_self_assessment_create_for_draft_goal_error(self):
        """Тест создания самооценки для цели в статусе черновика (должно быть ошибкой)"""
        self.client.force_authenticate(user=self.__class__.employee_user)

        data = {
            'rating': 7,
            'comments': 'Draft Goal Assessment',
            'areas_to_improve': 'Areas to Improve for Draft'
        }

        response = self.client.post(self.draft_assessment_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Проверяем, что самооценка не создана
        self.assertFalse(
            SelfAssessment.objects.filter(goal=self.draft_goal).exists())

    def test_self_assessment_create_duplicate_error(self):
        """Тест создания дубликата самооценки (должно быть ошибкой)"""
        # Создаем первую самооценку
        SelfAssessment.objects.create(
            goal=self.goal,
            rating=8,
            comments='Initial Assessment',
            areas_to_improve='Initial Areas to Improve'
        )

        self.client.force_authenticate(user=self.__class__.employee_user)

        data = {
            'rating': 9,
            'comments': 'Duplicate Assessment',
            'areas_to_improve': 'More Areas to Improve'
        }

        response = self.client.post(self.assessment_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Проверяем, что вторая самооценка не создана
        self.assertEqual(SelfAssessment.objects.filter(goal=self.goal).count(),
                         1)

    def test_self_assessment_create_by_other_employee_forbidden(self):
        """Тест создания самооценки другим сотрудником (должно быть запрещено)"""
        self.client.force_authenticate(user=self.__class__.employee2_user)

        data = {
            'rating': 6,
            'comments': 'Other Employee Assessment',
            'areas_to_improve': 'Areas from Other Employee'
        }

        response = self.client.post(self.assessment_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Проверяем, что самооценка не создана
        self.assertEqual(SelfAssessment.objects.count(), 0)

    def test_self_assessment_create_by_manager(self):
        """Тест создания самооценки руководителем"""
        self.client.force_authenticate(user=self.__class__.manager_user)

        data = {
            'rating': 8,
            'comments': 'Manager Assessment',
            'areas_to_improve': 'Manager Suggestions'
        }

        response = self.client.post(self.assessment_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Проверяем, что самооценка создана руководителем
        assessment = SelfAssessment.objects.first()
        self.assertEqual(assessment.comments, 'Manager Assessment')

    def test_self_assessment_retrieve_success(self):
        """Тест получения информации о самооценке"""
        # Создаем самооценку
        assessment = SelfAssessment.objects.create(
            goal=self.goal,
            rating=8,
            comments='Test Assessment',
            areas_to_improve='Test Areas to Improve'
        )

        self.client.force_authenticate(user=self.__class__.employee_user)

        url = reverse('goal-self-assessment-detail', kwargs={
            'goal_pk': self.goal.pk,
            'pk': assessment.pk
        })

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['rating'], 8)
        self.assertEqual(response.data['comments'], 'Test Assessment')

    def test_self_assessment_retrieve_by_manager(self):
        """Тест получения информации о самооценке руководителем"""
        # Создаем самооценку
        assessment = SelfAssessment.objects.create(
            goal=self.goal,
            rating=8,
            comments='Test Assessment',
            areas_to_improve='Test Areas to Improve'
        )

        self.client.force_authenticate(user=self.__class__.manager_user)

        url = reverse('goal-self-assessment-detail', kwargs={
            'goal_pk': self.goal.pk,
            'pk': assessment.pk
        })

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_self_assessment_retrieve_by_other_employee_forbidden(self):
        """Тест получения информации о самооценке другим сотрудником (должно быть запрещено)"""
        # Создаем самооценку
        assessment = SelfAssessment.objects.create(
            goal=self.goal,
            rating=8,
            comments='Test Assessment',
            areas_to_improve='Test Areas to Improve'
        )

        self.client.force_authenticate(user=self.__class__.employee2_user)

        url = reverse('goal-self-assessment-detail', kwargs={
            'goal_pk': self.goal.pk,
            'pk': assessment.pk
        })

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_self_assessment_update_success(self):
        """Тест успешного обновления самооценки"""
        # Создаем самооценку
        assessment = SelfAssessment.objects.create(
            goal=self.goal,
            rating=7,
            comments='Initial Assessment',
            areas_to_improve='Initial Areas'
        )

        self.client.force_authenticate(user=self.__class__.employee_user)

        url = reverse('goal-self-assessment-detail', kwargs={
            'goal_pk': self.goal.pk,
            'pk': assessment.pk
        })

        data = {
            'rating': 9,
            'comments': 'Updated Assessment',
            'areas_to_improve': 'Updated Areas'
        }

        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что самооценка обновлена
        assessment.refresh_from_db()
        self.assertEqual(assessment.rating, 9)
        self.assertEqual(assessment.comments, 'Updated Assessment')

    def test_self_assessment_update_by_manager(self):
        """Тест обновления самооценки руководителем"""
        # Создаем самооценку
        assessment = SelfAssessment.objects.create(
            goal=self.goal,
            rating=7,
            comments='Initial Assessment',
            areas_to_improve='Initial Areas'
        )

        self.client.force_authenticate(user=self.__class__.manager_user)

        url = reverse('goal-self-assessment-detail', kwargs={
            'goal_pk': self.goal.pk,
            'pk': assessment.pk
        })

        data = {
            'rating': 8,
            'comments': 'Manager Updated',
            'areas_to_improve': 'Manager Suggestions'
        }

        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что самооценка обновлена руководителем
        assessment.refresh_from_db()
        self.assertEqual(assessment.rating, 8)
        self.assertEqual(assessment.comments, 'Manager Updated')

    def test_self_assessment_update_by_other_employee_forbidden(self):
        """Тест обновления самооценки другим сотрудником (должно быть запрещено)"""
        # Создаем самооценку
        assessment = SelfAssessment.objects.create(
            goal=self.goal,
            rating=7,
            comments='Initial Assessment',
            areas_to_improve='Initial Areas'
        )

        self.client.force_authenticate(user=self.__class__.employee2_user)

        url = reverse('goal-self-assessment-detail', kwargs={
            'goal_pk': self.goal.pk,
            'pk': assessment.pk
        })

        data = {
            'rating': 5,
            'comments': 'Other Employee Updated',
            'areas_to_improve': 'Other Employee Suggestions'
        }

        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Проверяем, что самооценка не обновлена
        assessment.refresh_from_db()
        self.assertEqual(assessment.rating, 7)
        self.assertEqual(assessment.comments, 'Initial Assessment')
