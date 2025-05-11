from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from accounts.urls import api_router as accounts_api_router

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui'
    ),

    path('api/auth/', include('accounts.urls')),
    path('api/', include(accounts_api_router.urls)),

    # path('api/', include('goals.urls')),
    # path('api/', include('feedback.urls')),
]
