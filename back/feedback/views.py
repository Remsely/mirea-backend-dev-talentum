from django.shortcuts import render
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated

from goals.models import Goal
from goals.permissions import IsEmployeeOwnerOrManagerOrExpertiseLeaderOrAdmin
from .models import SelfAssessment
from .serializers import SelfAssessmentSerializer


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
