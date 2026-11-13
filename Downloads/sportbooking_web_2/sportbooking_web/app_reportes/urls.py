from django.urls import path
from . import views

app_name = 'app_reportes'
urlpatterns = [
    path('', views.panel_reportes, name='inicio'),
    path('panel/', views.panel_reportes, name='panel_reportes'),
    path('exportar/excel/', views.exportar_excel, name='exportar_excel'),
    path('exportar/pdf/', views.exportar_pdf, name='exportar_pdf'),
]
