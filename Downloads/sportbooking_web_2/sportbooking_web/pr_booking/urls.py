from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('usuarios/', include('app_usuarios.urls')),
    path('reservas/', include('app_reservas.urls')),
    path('reportes/', include('app_reportes.urls')),
    path('tickets/', include('app_tickets.urls')),
    path('', include('app_escenarios.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
