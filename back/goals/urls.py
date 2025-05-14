from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter

from .views import GoalViewSet, ProgressViewSet

router = DefaultRouter()
router.register('goals', GoalViewSet, basename='goal')

progress_router = NestedDefaultRouter(router, 'goals', lookup='goal')
progress_router.register('progress', ProgressViewSet, basename='goal-progress')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(progress_router.urls)),
]
