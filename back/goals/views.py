from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets, mixins, status, filters
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import Employee
from .filters import GoalFilterSet
from .models import Goal, Progress
from .permissions import (
    IsEmployeeOwnerOrManagerOrExpertiseLeaderOrAdmin, IsManager, CanManageGoal
)
from .serializers import (
    GoalListSerializer, GoalDetailSerializer, GoalCreateSerializer,
    GoalUpdateSerializer, ProgressSerializer
)


@extend_schema_view(
    list=extend_schema(
        description="Получение списка целей с учетом прав доступа",
        tags=['goals']
    ),
    retrieve=extend_schema(
        description="Получение детальной информации о цели",
        tags=['goals']
    ),
    create=extend_schema(
        description="Создание новой цели (в статусе черновика)",
        tags=['goals']
    ),
    update=extend_schema(
        description="Обновление существующей цели "
                    "(только в статусе черновика)",
        tags=['goals']
    ),
    partial_update=extend_schema(
        description="Частичное обновление цели (только в статусе черновика)",
        tags=['goals']
    ),
    destroy=extend_schema(
        description="Удаление цели (только в статусе черновика)",
        tags=['goals']
    ),
)
class GoalViewSet(viewsets.ModelViewSet):
    queryset = Goal.objects.all().select_related(
        'employee',
        'employee__user'
    ).prefetch_related(
        'progress_entries'
    )
    permission_classes = [IsAuthenticated, CanManageGoal]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = GoalFilterSet
    search_fields = ['title', 'description']

    def get_serializer_class(self):
        if self.action == 'create':
            return GoalCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return GoalUpdateSerializer
        elif self.action == 'list':
            return GoalListSerializer
        return GoalDetailSerializer

    def get_queryset(self):
        user = self.request.user

        if user.role == 'admin':
            return self.queryset

        try:
            employee = user.employee_profile

            employee_goals = Q(employee=employee)

            if employee.subordinates.exists():
                all_subordinates = self._get_all_subordinates(employee)
                subordinate_goals = Q(employee__in=all_subordinates)
                return self.queryset.filter(employee_goals | subordinate_goals)

            if user.role == 'expertise_leader':
                return self.queryset.filter(
                    employee_goals | Q(status=Goal.STATUS_PENDING_ASSESSMENT)
                )

            return self.queryset.filter(employee_goals)

        except Employee.DoesNotExist:
            return self.queryset.none()

    def _get_all_subordinates(self, employee):
        """Рекурсивно получает всех подчиненных (прямых и косвенных)"""
        all_subordinates = list(employee.subordinates.all())
        for sub in employee.subordinates.all():
            all_subordinates.extend(self._get_all_subordinates(sub))
        return all_subordinates

    def perform_create(self, serializer):
        try:
            serializer.save()
        except Employee.DoesNotExist:
            raise PermissionDenied(
                "У вас нет профиля сотрудника для создания целей"
            )

    def perform_destroy(self, instance):
        if instance.status != Goal.STATUS_DRAFT:
            raise PermissionDenied(
                "Можно удалять только цели в статусе черновика"
            )
        instance.delete()

    @extend_schema(
        tags=['goals'],
        description="Отправка цели на согласование"
    )
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        goal = self.get_object()

        if not goal.can_be_submitted():
            raise PermissionDenied(
                "Цель не может быть отправлена на согласование"
            )
        if not goal.employee.manager:
            return Response(
                {
                    "detail": "У вас нет руководителя для согласования"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        goal.status = Goal.STATUS_PENDING_APPROVAL
        goal.save()

        serializer = GoalDetailSerializer(
            goal,
            context={
                'request': request
            }
        )
        return Response(serializer.data)

    @extend_schema(
        tags=['goals'],
        description="Одобрение цели руководителем"
    )
    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated, IsManager]
    )
    def approve(self, request, pk=None):
        goal = self.get_object()

        if not goal.can_be_approved():
            raise ValidationError(
                "Цель не может быть согласована"
            )

        try:
            manager = request.user.employee_profile

            if goal.employee.manager != manager:
                raise PermissionDenied(
                    "Вы не являетесь руководителем этого сотрудника"
                )

            goal.status = Goal.STATUS_IN_PROGRESS
            goal.save()

            serializer = GoalDetailSerializer(
                goal,
                context={
                    'request': request
                }
            )
            return Response(serializer.data)

        except Employee.DoesNotExist:
            raise PermissionDenied("У вас нет профиля сотрудника")

    @extend_schema(
        tags=['goals'],
        description="Завершение выполнения цели"
    )
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        goal = self.get_object()

        if not goal.can_complete():
            raise PermissionDenied(
                "Цель не может быть завершена"
            )

        goal.status = Goal.STATUS_PENDING_ASSESSMENT
        goal.save()

        serializer = GoalDetailSerializer(
            goal,
            context={
                'request': request
            }
        )
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        description="Получение списка записей о прогрессе по цели",
        tags=['progress']
    ),
    create=extend_schema(
        description="Добавление новой записи о прогрессе",
        tags=['progress']
    ),
)
class ProgressViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = ProgressSerializer
    permission_classes = [IsAuthenticated,
                          IsEmployeeOwnerOrManagerOrExpertiseLeaderOrAdmin]

    def get_queryset(self):
        goal_id = self.kwargs.get('goal_pk')
        return (
            Progress.objects
            .filter(goal_id=goal_id)
            .order_by('-created_dttm')
        )

    def perform_create(self, serializer):
        goal_id = self.kwargs.get('goal_pk')
        goal = Goal.objects.get(id=goal_id)

        try:
            self.check_object_permissions(self.request, goal)
        except PermissionDenied:
            raise PermissionDenied(
                "У вас нет прав на добавление записей о прогрессе к этой цели")

        if not goal.can_add_progress():
            raise ValidationError(
                "К этой цели нельзя добавлять записи о прогрессе"
            )

        serializer.save(goal_id=goal_id)
