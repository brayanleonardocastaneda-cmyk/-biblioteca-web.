from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils.http import url_has_allowed_host_and_scheme

from .models import Cliente, Usuario


def _destino(request, user):
    siguiente = request.POST.get('next') or request.GET.get('next')
    if siguiente and url_has_allowed_host_and_scheme(siguiente, {request.get_host()}):
        return siguiente
    return 'app_escenarios:panel_canchas' if user.is_staff else 'app_escenarios:catalogo'


def login_view(request):
    if request.user.is_authenticated:
        return redirect(_destino(request, request.user))
    if request.method == 'POST':
        email = (request.POST.get('email') or request.POST.get('username') or '').strip().lower()
        if Usuario.iniciar_sesion(request, email, request.POST.get('password')):
            return redirect(_destino(request, request.user))
        return render(request, 'usuarios/login.html', {'error': 'Correo o contraseña incorrectos', 'email': email})
    return render(request, 'usuarios/login.html')


def login_google(request):
    """El botón existe como en el prototipo, pero Google necesita credenciales propias (OAuth)."""
    messages.error(request, 'El ingreso con Google aún no está configurado. Usa tu correo y contraseña.')
    return redirect('app_usuarios:login')


def logout_view(request):
    Usuario.cerrar_sesion(request)
    return redirect('app_usuarios:login')


def registrar_usuario(request):
    datos = {}
    if request.method == 'POST':
        datos = {k: request.POST.get(k, '').strip() for k in ('nombre', 'email', 'telefono')}
        datos['email'] = datos['email'].lower()
        password = request.POST.get('password', '')
        if not (datos['nombre'] and datos['email'] and password):
            datos['error'] = 'Completa nombre, correo y contraseña.'
        elif len(password) < 8:
            datos['error'] = 'La contraseña debe tener al menos 8 caracteres.'
        elif password != request.POST.get('password2', ''):
            datos['error'] = 'Las contraseñas no coinciden.'
        elif not Cliente.registrar_usuario(datos['nombre'], datos['email'], password, datos['telefono']):
            datos['error'] = 'Ya existe una cuenta con ese correo.'
        else:
            Usuario.iniciar_sesion(request, datos['email'], password)
            messages.success(request, f'¡Bienvenido, {datos["nombre"]}!')
            return redirect('app_escenarios:catalogo')
    return render(request, 'usuarios/registro.html', datos)


def panel_admin_view(request):
    return redirect('app_escenarios:panel_canchas')
