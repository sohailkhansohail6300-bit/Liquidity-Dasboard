from django.conf import settings
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.permissions import AllowAny
from django.contrib import admin
from django.urls import path
from core.permissions import IsAdminRole

_docs_permission = [AllowAny] if settings.API_DOCS_PUBLIC else [IsAdminRole]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(permission_classes=_docs_permission), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema', permission_classes=_docs_permission), name='docs'),
    path('api/', include('core.urls')),
    path('api/', include('accounts.urls')),
    path('api/', include('companies.urls')),
    path('api/', include('market.urls')),
    path('api/', include('subscriptions.urls')),
    path('api/', include('support.urls')),
    path('api/', include('administration.urls')),
]
