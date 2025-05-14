from django.urls import path, include
from rest_framework_nested.routers import NestedDefaultRouter

from goals.urls import router as goals_router
from .views import SelfAssessmentViewSet

self_assessment_router = NestedDefaultRouter(goals_router, 'goals', lookup='goal')
self_assessment_router.register(
    'self-assessment',
    SelfAssessmentViewSet,
    basename='goal-self-assessment'
)

urlpatterns = [
    path('', include(self_assessment_router.urls)),
] 