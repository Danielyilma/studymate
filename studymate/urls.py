from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('sessions/', include('study_tools.urls')),
    path('users/', include('UserAccountManager.urls')),
]
 

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)