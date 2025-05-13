from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter

from .views import GoalViewSet, ProgressViewSet, SelfAssessmentViewSet

router = DefaultRouter()
router.register('goals', GoalViewSet, basename='goal')

progress_router = NestedDefaultRouter(router, 'goals', lookup='goal')
progress_router.register('progress', ProgressViewSet, basename='goal-progress')

self_assessment_router = NestedDefaultRouter(router, 'goals', lookup='goal')
self_assessment_router.register(
    'self-assessment',
    SelfAssessmentViewSet,
    basename='goal-self-assessment'
)

urlpatterns = [
    path('', include(router.urls)),
    path('', include(progress_router.urls)),
    path('', include(self_assessment_router.urls)),
]
