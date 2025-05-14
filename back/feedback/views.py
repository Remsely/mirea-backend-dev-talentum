from django.shortcuts import render, get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from goals.models import Goal
from goals.permissions import IsEmployeeOwnerOrManagerOrExpertiseLeaderOrAdmin
from .models import SelfAssessment, FeedbackRequest, PeerFeedback, ExpertEvaluation
from .permissions import CanRequestFeedback, CanProvideFeedback, CanProvideExpertEvaluation
from .serializers import (
    SelfAssessmentSerializer, FeedbackRequestListSerializer, 
    FeedbackRequestCreateSerializer, PeerFeedbackSerializer, 
    ExpertEvaluationSerializer
)


@extend_schema_view(
    retrieve=extend_schema(
        description="Получение информации о самооценке по цели",
        tags=['self-assessment']
    ),
    create=extend_schema(
        description="Добавление самооценки по цели",
        tags=['self-assessment']
    ),
    update=extend_schema(
        description="Обновление самооценки по цели",
        tags=['self-assessment']
    ),
    partial_update=extend_schema(
        description="Частичное обновление самооценки по цели",
        tags=['self-assessment']
    ),
)
class SelfAssessmentViewSet(
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = SelfAssessmentSerializer
    permission_classes = [IsAuthenticated,
                          IsEmployeeOwnerOrManagerOrExpertiseLeaderOrAdmin]

    def get_queryset(self):
        goal_id = self.kwargs.get('goal_pk')
        return SelfAssessment.objects.filter(goal_id=goal_id)

    def get_object(self):
        goal_id = self.kwargs.get('goal_pk')
        try:
            obj = SelfAssessment.objects.get(goal_id=goal_id)
            self.check_object_permissions(self.request, obj)
            return obj
        except SelfAssessment.DoesNotExist:
            raise ValidationError("Самооценка для этой цели не найдена")

    def perform_create(self, serializer):
        goal_id = self.kwargs.get('goal_pk')
        goal = Goal.objects.get(id=goal_id)

        try:
            self.check_object_permissions(self.request, goal)
        except PermissionDenied:
            raise PermissionDenied(
                "У вас нет прав на добавление самооценки к этой цели")

        if not goal.can_add_self_assessment():
            raise ValidationError("К этой цели нельзя добавлять самооценку")

        if SelfAssessment.objects.filter(goal_id=goal_id).exists():
            raise ValidationError("Самооценка для этой цели уже существует")

        serializer.save(goal_id=goal_id)


@extend_schema_view(
    list=extend_schema(
        description="Получение списка запросов отзывов для цели",
        tags=['feedback']
    ),
    create=extend_schema(
        description="Создание нового запроса отзыва для цели",
        tags=['feedback']
    ),
    retrieve=extend_schema(
        description="Получение информации о запросе отзыва",
        tags=['feedback']
    ),
)
class FeedbackRequestViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated(), CanRequestFeedback()]
        return [IsAuthenticated()]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return FeedbackRequestCreateSerializer
        return FeedbackRequestListSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['goal_id'] = self.kwargs.get('goal_pk')
        return context
    
    def get_queryset(self):
        goal_id = self.kwargs.get('goal_pk')
        user = self.request.user

        queryset = FeedbackRequest.objects.filter(goal_id=goal_id)

        if user.role not in ['admin', 'expertise_leader']:
            try:
                employee = user.employee_profile

                is_reviewer = FeedbackRequest.objects.filter(
                    goal_id=goal_id, reviewer=employee).exists()
                is_requester = Goal.objects.filter(
                    id=goal_id, employee=employee).exists()
                
                if not (is_reviewer or is_requester):
                    goal = Goal.objects.get(id=goal_id)
                    if goal.employee.manager != employee:
                        if self.action in ['list', 'retrieve']:
                            self.permission_denied(
                                self.request,
                                message="У вас нет прав на просмотр запросов отзывов для этой цели"
                            )
                        return FeedbackRequest.objects.none()
            except:
                if self.action in ['list', 'retrieve']:
                    self.permission_denied(
                        self.request,
                        message="У вас нет доступа к этому ресурсу"
                    )
                return FeedbackRequest.objects.none()
                
        return queryset
    
    def perform_create(self, serializer):
        goal_id = self.kwargs.get('goal_pk')
        goal = get_object_or_404(Goal, id=goal_id)

        self.check_object_permissions(self.request, goal)

        serializer.save(goal_id=goal_id)


@extend_schema_view(
    list=extend_schema(
        description="Получение списка запросов отзывов для текущего пользователя",
        tags=['feedback']
    )
)
class MyFeedbackRequestsViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = FeedbackRequestListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        try:
            employee = user.employee_profile
            return FeedbackRequest.objects.filter(
                reviewer=employee,
                status=FeedbackRequest.STATUS_PENDING
            ).order_by('-created_dttm')
        except:
            return FeedbackRequest.objects.none()


@extend_schema_view(
    create=extend_schema(
        description="Предоставление отзыва по запросу",
        tags=['feedback']
    ),
    retrieve=extend_schema(
        description="Получение информации об отзыве",
        tags=['feedback']
    ),
)
class PeerFeedbackViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = PeerFeedbackSerializer
    permission_classes = [IsAuthenticated, CanProvideFeedback]
    
    def get_queryset(self):
        feedback_request_id = self.kwargs.get('request_pk')
        return PeerFeedback.objects.filter(feedback_request_id=feedback_request_id)
    
    def get_feedback_request(self):
        feedback_request_id = self.kwargs.get('request_pk')
        feedback_request = get_object_or_404(
            FeedbackRequest, id=feedback_request_id)
        self.check_object_permissions(self.request, feedback_request)
        return feedback_request
    
    def perform_create(self, serializer):
        feedback_request = self.get_feedback_request()

        if PeerFeedback.objects.filter(feedback_request=feedback_request).exists():
            raise ValidationError("Отзыв для этого запроса уже существует")
        
        serializer.save(feedback_request=feedback_request)


@extend_schema_view(
    retrieve=extend_schema(
        description="Получение информации об экспертной оценке",
        tags=['expert-evaluation']
    ),
    create=extend_schema(
        description="Добавление экспертной оценки по цели",
        tags=['expert-evaluation']
    ),
)
class ExpertEvaluationViewSet(
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = ExpertEvaluationSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated(), CanProvideExpertEvaluation()]
        return [IsAuthenticated()]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['goal_id'] = self.kwargs.get('goal_pk')
        return context
    
    def get_queryset(self):
        goal_id = self.kwargs.get('goal_pk')
        user = self.request.user
        
        if self.action == 'retrieve' and self.request.user.is_authenticated:
            # Allow employees to view their own goals' evaluations
            try:
                goal = Goal.objects.get(id=goal_id)
                if goal.employee.user == self.request.user or \
                   user.role in ['admin', 'expertise_leader'] or \
                   (goal.employee.manager and goal.employee.manager.user == self.request.user):
                    return ExpertEvaluation.objects.filter(goal_id=goal_id)
            except Goal.DoesNotExist:
                pass
                
        return ExpertEvaluation.objects.filter(goal_id=goal_id)
    
    def get_object(self):
        goal_id = self.kwargs.get('goal_pk')
        try:
            obj = ExpertEvaluation.objects.get(goal_id=goal_id)
            return obj
        except ExpertEvaluation.DoesNotExist:
            raise ValidationError("Экспертная оценка для этой цели не найдена")
    
    def perform_create(self, serializer):
        goal_id = self.kwargs.get('goal_pk')
        goal = get_object_or_404(Goal, id=goal_id)

        if self.action == 'create':
            self.check_object_permissions(self.request, goal)
        
        # Check for duplicate evaluation - always return 400 Bad Request
        if ExpertEvaluation.objects.filter(goal=goal).exists():
            raise ValidationError({"non_field_errors": ["Экспертная оценка для этой цели уже существует"]})
        
        if not SelfAssessment.objects.filter(goal=goal).exists():
            raise ValidationError("Самооценка для этой цели еще не создана")
        
        if not PeerFeedback.objects.filter(feedback_request__goal=goal).exists():
            raise ValidationError("Для этой цели еще не предоставлено ни одного отзыва от коллег")
        
        serializer.save(goal_id=goal_id)
