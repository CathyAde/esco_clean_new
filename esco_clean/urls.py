from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from main.admin import admin_site

urlpatterns = [
    # Administration ESCO personnalisée
    path('admin/', admin_site.urls),
    
    # URLs de l'application principale
    path('', include('main.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)