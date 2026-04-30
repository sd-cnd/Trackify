from django.contrib import admin
from django.urls import path, include, re_path
from django.http import HttpResponse
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt.views import TokenRefreshView


# Swagger configuration
schema_view = get_schema_view(
    openapi.Info(
        title="Trackify API",
        default_version='v1',
        description="HRMS System APIs (Attendance + Leave + Projects)",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    patterns=[
        path('api/accounts/', include('accounts.urls')),
        path('api/projects/', include('projects.urls')),
        path('api/attendance/', include('attendance.urls')),
        path('api/leaves/', include('leaves.urls')),
    ],
)


# Home view
def home_view(request):
    html = """
    <html>
        <head>
            <title>Trackify API</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; }
                h1 { color: #333; }
                ul { list-style: none; padding: 0; }
                li { margin: 12px 0; }
                a { text-decoration: none; color: #0077cc; font-size: 16px; }
                a:hover { text-decoration: underline; }
                .section { margin-top: 20px; }
                h3 { color: #555; border-bottom: 1px solid #ddd; padding-bottom: 5px; }
            </style>
        </head>
        <body>
            <h1>🔗 Trackify API</h1>

            <div class="section">
                <h3>📄 API Docs</h3>
                <ul>
                    <li><a href="/api/docs/">Swagger UI</a></li>
                    <li><a href="/api/redoc/">ReDoc</a></li>
                </ul>
            </div>

            <div class="section">
                <h3>🔗 API Endpoints</h3>
                <ul>
                    <li><a href="/api/accounts/">Accounts</a></li>
                    <li><a href="/api/projects/">Projects</a></li>
                    <li><a href="/api/attendance/">Attendance</a></li>
                    <li><a href="/api/leaves/">Leaves</a></li>
                </ul>
            </div>
        </body>
    </html>
    """
    return HttpResponse(html)


urlpatterns = [
    path('admin/', admin.site.urls),

    # Home
    path('', home_view, name='home'),

    # path('api-auth/', include('rest_framework.urls')),

    # JWT token refresh
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    # Accounts (auth + employees)
    path('api/accounts/', include('accounts.urls')),

    # Projects
    path('api/projects/', include('projects.urls')),

    # Attendance
    path('api/attendance/', include('attendance.urls')),

    # Leaves
    path('api/leaves/', include('leaves.urls')),

    # Swagger / API Docs
    re_path(r'^api/docs(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^api/docs/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^api/redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]