from django.urls import path
from rest_framework.routers import DefaultRouter

from accounts.views import UserViewSet, EmployeeViewSet, \
    CustomTokenObtainPairView, CustomTokenRefreshView

auth_router = DefaultRouter()

api_router = DefaultRouter()
api_router.register(r'users', UserViewSet)
api_router.register(r'employees', EmployeeViewSet)

urlpatterns = [
    path(
        'token/',
        CustomTokenObtainPairView.as_view(),
        name='token_obtain_pair'
    ),
    path(
        'token/refresh/',
        CustomTokenRefreshView.as_view(),
        name='token_refresh'
    ),
]
