from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy
from . import views

app_name = 'app_usuarios'
urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('login/google/', views.login_google, name='login_google'),
    path('logout/', views.logout_view, name='logout'),
    path('registro/', views.registrar_usuario, name='registro'),
    path('panel/', views.panel_admin_view, name='panel_admin'),
    # Recuperar contraseña con las vistas que ya trae Django
    path('recuperar/', auth_views.PasswordResetView.as_view(
        template_name='usuarios/password_reset.html',
        email_template_name='usuarios/password_reset_email.txt',
        subject_template_name='usuarios/password_reset_subject.txt',
        success_url=reverse_lazy('app_usuarios:password_reset_done'),
    ), name='password_reset'),
    path('recuperar/enviado/', auth_views.PasswordResetDoneView.as_view(
        template_name='usuarios/password_reset_done.html'), name='password_reset_done'),
    path('recuperar/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='usuarios/password_reset_confirm.html',
        success_url=reverse_lazy('app_usuarios:login'),
        post_reset_login=False,
    ), name='password_reset_confirm'),
]
