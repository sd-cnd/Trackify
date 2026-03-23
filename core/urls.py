from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Accounts (auth + employees)
    path('api/accounts/', include('accounts.urls')),

    # Projects
    path('api/projects/', include('projects.urls')),
    path("api/attendance/", include("attendance.urls")),
]