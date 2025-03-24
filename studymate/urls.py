from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('courses/', include('study_tools.urls')),
    path('users/', include('UserAccountManager.urls')),
]
 