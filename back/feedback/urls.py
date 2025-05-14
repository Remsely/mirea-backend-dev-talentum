from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter

from goals.urls import router as goals_router
from .views import (
    SelfAssessmentViewSet, FeedbackRequestViewSet, 
    MyFeedbackRequestsViewSet, PeerFeedbackViewSet, 
    ExpertEvaluationViewSet
)

self_assessment_router = NestedDefaultRouter(goals_router, 'goals', lookup='goal')
self_assessment_router.register(
    'self-assessment',
    SelfAssessmentViewSet,
    basename='goal-self-assessment'
)

feedback_request_router = NestedDefaultRouter(goals_router, 'goals', lookup='goal')
feedback_request_router.register(
    'feedback-requests',
    FeedbackRequestViewSet,
    basename='goal-feedback-request'
)

peer_feedback_router = NestedDefaultRouter(feedback_request_router, 'feedback-requests', lookup='request')
peer_feedback_router.register(
    'feedback',
    PeerFeedbackViewSet,
    basename='feedback-request-feedback'
)

expert_evaluation_router = NestedDefaultRouter(goals_router, 'goals', lookup='goal')
expert_evaluation_router.register(
    'expert-evaluation',
    ExpertEvaluationViewSet,
    basename='goal-expert-evaluation'
)

my_feedback_requests_router = NestedDefaultRouter(goals_router, 'goals', lookup='goal')
my_feedback_requests_router.register(
    'my-feedback-requests',
    MyFeedbackRequestsViewSet,
    basename='my-feedback-requests'
)

urlpatterns = [
    path('', include(self_assessment_router.urls)),
    path('', include(feedback_request_router.urls)),
    path('', include(peer_feedback_router.urls)),
    path('', include(expert_evaluation_router.urls)),
    path('', include(my_feedback_requests_router.urls)),
]
