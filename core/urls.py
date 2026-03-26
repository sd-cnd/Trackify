from django.contrib import admin
from django.urls import path, include, re_path

# Swagger imports
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


# Swagger configuration
schema_view = get_schema_view(
    openapi.Info(
        title="Trackify API",
        default_version='v1',
        description="HRMS System APIs (Attendance + Leave + Projects)",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)


urlpatterns = [
    path('admin/', admin.site.urls),

    # Accounts (auth + employees)
    path('api/accounts/', include('accounts.urls')),

    # Projects
    path('api/projects/', include('projects.urls')),

    # Attendance
    path("api/attendance/", include("attendance.urls")),

    # Leaves
    path("api/leaves/", include("leaves.urls")),

    # -----------------------------
    # Swagger / API Docs
    # -----------------------------
    re_path(r'^api/docs/$', schema_view.with_ui('swagger', cache_timeout=0)),
    re_path(r'^api/redoc/$', schema_view.with_ui('redoc', cache_timeout=0)),
]
