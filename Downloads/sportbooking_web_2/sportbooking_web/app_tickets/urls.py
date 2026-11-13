from django.urls import path
from . import views

app_name = 'app_tickets'
urlpatterns = [
    path('generar/<int:reserva_id>/', views.generar_ticket, name='generar_ticket'),
    path('validar/', views.validar_qr_view, name='validar_qr'),
    path('panel/', views.panel_validador, name='panel_validador'),
    path('validar-ticket/', views.validar_ticket, name='validar_ticket'),
]
