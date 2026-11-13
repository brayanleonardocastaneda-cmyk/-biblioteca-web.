from django.urls import path
from . import views

app_name = 'app_escenarios'
urlpatterns = [
    # Cliente
    path('', views.listar_escenarios, name='listar_escenarios'),
    path('catalogo/', views.catalogo, name='catalogo'),
    path('explorar/', views.explorar_canchas, name='explorar'),
    path('cancha/<int:pk>/', views.detalle_escenario, name='escenario_detalle'),
    path('detalle/<int:pk>/', views.detalle_cancha, name='detalle_cancha'),
    path('horarios/<int:pk>/', views.horarios_disponibles, name='horarios_disponibles'),
    path('cancha/<int:pk>/resena/', views.publicar_resena, name='publicar_resena'),
    # Administrador
    path('panel/canchas/', views.panel_canchas, name='panel_canchas'),
    path('panel/canchas/lista/', views.lista_escenarios_admin, name='lista_escenarios_admin'),
    path('panel/canchas/crear/', views.crear_escenario, name='cancha_crear'),
    path('crear/', views.crear_escenario, name='crear_escenario'),
    path('panel/canchas/editar/<int:pk>/', views.editar_escenario, name='editar_escenario'),
    path('panel/canchas/estado/<int:pk>/', views.cambiar_estado_escenario, name='cambiar_estado'),
    path('panel/canchas/eliminar/<int:pk>/', views.eliminar_escenario, name='eliminar_escenario'),
]
