from django.contrib.auth import get_user_model
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter, \
    extend_schema_view
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, \
    TokenRefreshView

from accounts.models import Employee
from accounts.permissions import IsAdminOrSelf, IsAdminOnly, \
    IsEmployeeOwnerOrAdmin
from accounts.serializers import CustomTokenObtainPairSerializer, \
    UserSerializer, UserCreateSerializer, UserDetailSerializer, \
    EmployeeSerializer, EmployeeDetailSerializer, \
    EmployeeCreateUpdateSerializer

User = get_user_model()


@extend_schema(tags=['auth'])
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


@extend_schema(tags=['auth'])
class CustomTokenRefreshView(TokenRefreshView):
    pass


@extend_schema_view(
    list=extend_schema(
        description="Получение списка всех пользователей системы",
        tags=['users']
    ),
    retrieve=extend_schema(
        description="Получение детальной информации о пользователе по ID",
        tags=['users']
    ),
    create=extend_schema(
        description="Создание нового пользователя в системе",
        tags=['users']
    ),
    update=extend_schema(
        description="Полное обновление данных пользователя",
        tags=['users']
    ),
    partial_update=extend_schema(
        description="Частичное обновление данных пользователя",
        tags=['users']
    ),
    destroy=extend_schema(
        description="Удаление пользователя из системы",
        tags=['users']
    ),
)
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    filterset_fields = ['role', 'is_active']

    def get_permissions(self):
        if self.action in ['list', 'create', 'destroy', 'search']:
            permission_classes = [IsAdminOnly]
        elif self.action in ['update', 'partial_update', 'retrieve']:
            permission_classes = [IsAdminOrSelf]
        elif self.action == 'me':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action == 'retrieve' or self.action == 'me':
            return UserDetailSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        """Создание пользователя с возвратом полных данных, включая ID"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Используем DetailSerializer для ответа, чтобы включить ID
        response_serializer = UserDetailSerializer(user)
        return Response(response_serializer.data,
                        status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=['users'],
        parameters=[
            OpenApiParameter(
                name='q',
                description='Поисковый запрос',
                required=False,
                type=str
            )
        ],
        description="Поиск пользователей по имени, фамилии, username или email"
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAdminOnly])
    def search(self, request):
        query = request.query_params.get('q', '')
        if not query:
            return Response([])

        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )[:10]

        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    @extend_schema(
        description="Получение информации о текущем авторизованном пользователе",
        tags=['users']
    )
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        tags=['employees'],
        description="Получение списка всех сотрудников компании"
    ),
    retrieve=extend_schema(
        tags=['employees'],
        description="Получение детальной информации о конкретном сотруднике по ID"
    ),
    create=extend_schema(
        tags=['employees'],
        description="Создание нового профиля сотрудника для существующего пользователя"
    ),
    update=extend_schema(
        tags=['employees'],
        description="Полное обновление данных профиля сотрудника"
    ),
    partial_update=extend_schema(
        tags=['employees'],
        description="Частичное обновление данных профиля сотрудника"
    ),
    destroy=extend_schema(
        tags=['employees'],
        description="Удаление профиля сотрудника из системы"
    ),
)
class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['user__username', 'user__email', 'user__first_name',
                     'user__last_name', 'position']
    filterset_fields = ['position', 'manager']

    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            permission_classes = [IsAdminOnly]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [IsEmployeeOwnerOrAdmin]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return EmployeeDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return EmployeeCreateUpdateSerializer
        return EmployeeSerializer

    @extend_schema(
        tags=['employees'],
        description="Получение информации о профиле текущего авторизованного сотрудника"
    )
    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        try:
            employee = request.user.employee_profile
            serializer = EmployeeDetailSerializer(employee)
            return Response(serializer.data)
        except Employee.DoesNotExist:
            return Response(
                {"detail": "У вас нет профиля сотрудника"},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        tags=['employees'],
        description="Получение списка всех подчиненных текущего сотрудника (на всех уровнях иерархии)",
        parameters=[
            OpenApiParameter(
                name='levels',
                description='Количество уровней иерархии для поиска подчиненных (по умолчанию все)',
                required=False,
                type=int
            )
        ]
    )
    @action(detail=False, methods=['get'])
    def my_team(self, request):
        try:
            employee = request.user.employee_profile

            levels = request.query_params.get('levels', None)

            direct_subordinates = employee.subordinates.all()

            if not levels or int(levels) <= 1:
                serializer = EmployeeSerializer(direct_subordinates, many=True)
                return Response(serializer.data)

            all_subordinates = list(direct_subordinates)
            current_level = list(direct_subordinates)
            current_level_number = 1
            max_levels = int(levels)

            while current_level and current_level_number < max_levels:
                next_level = []
                for sub in current_level:
                    next_level.extend(sub.subordinates.all())

                all_subordinates.extend(next_level)
                current_level = next_level
                current_level_number += 1

            unique_subordinates = list(
                {sub.id: sub for sub in all_subordinates}.values())

            serializer = EmployeeSerializer(unique_subordinates, many=True)
            return Response(serializer.data)

        except Employee.DoesNotExist:
            return Response(
                {"detail": "У вас нет профиля сотрудника"},
                status=status.HTTP_404_NOT_FOUND
            )
