from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST

from app_usuarios.models import Administrador
from app_usuarios.permisos import solo_admin
from .forms import EscenarioForm
from .models import Escenario, Servicio, ImagenEscenario, Resena


# Tope del filtro "Precio máx / hora" en Explorar
PRECIO_MAXIMO = 200000


def listar_escenarios(request):
    """Página Explorar: catálogo de canchas con filtros."""
    canchas = Escenario.objects.filter(activo=True).prefetch_related('imagenes', 'servicios')
    deporte = request.GET.get('deporte', '')
    try:
        precio_max = int(request.GET.get('precio_max', PRECIO_MAXIMO))
    except ValueError:
        precio_max = PRECIO_MAXIMO
    servicios_sel = request.GET.getlist('servicio')
    busqueda = request.GET.get('q', '').strip()
    if deporte:
        canchas = canchas.filter(deporte=deporte)
    for servicio_id in servicios_sel:
        canchas = canchas.filter(servicios__id=servicio_id)
    if busqueda:
        canchas = canchas.filter(Q(nombre__icontains=busqueda) | Q(ubicacion__icontains=busqueda))
    canchas = canchas.filter(precio_hora__lte=precio_max)
    return render(request, 'app_escenarios/explorar.html', {
        'canchas': canchas.distinct(),
        'deportes': Escenario.DEPORTES,
        'servicios': Servicio.objects.all(),
        'deporte_actual': deporte,
        'servicios_sel': servicios_sel,
        'busqueda': busqueda,
        'precio_max': precio_max,
        'precio_tope': PRECIO_MAXIMO,
    })


catalogo = listar_escenarios
explorar_canchas = listar_escenarios


def _fecha_param(request):
    try:
        return date.fromisoformat(request.GET.get('fecha', ''))
    except ValueError:
        return date.today()


def detalle_escenario(request, pk):
    """Detalle de la cancha: fotos, bloques disponibles y reseñas."""
    cancha = get_object_or_404(Escenario, pk=pk)
    if not cancha.activo and not request.user.is_staff:
        messages.error(request, 'Esta cancha no está disponible en este momento.')
        return redirect('app_escenarios:catalogo')
    fecha = _fecha_param(request)
    mi_resena = None
    if request.user.is_authenticated:
        mi_resena = cancha.resenas.filter(usuario=request.user).first()
    return render(request, 'app_escenarios/detalle.html', {
        'cancha': cancha,
        'fecha': fecha,
        'hoy': date.today(),
        'horarios': cancha.obtener_horarios(fecha),
        'resenas': cancha.resenas.select_related('usuario'),
        'promedio': cancha.calificacion_promedio(),
        'resumen': cancha.resumen_calificaciones(),
        'mi_resena': mi_resena,
    })


escenario_detalle = detalle_escenario
detalle_cancha = detalle_escenario
horarios_disponibles = detalle_escenario


@login_required
@require_POST
def publicar_resena(request, pk):
    cancha = get_object_or_404(Escenario, pk=pk)
    try:
        calificacion = int(request.POST.get('calificacion', 0))
    except ValueError:
        calificacion = 0
    if not 1 <= calificacion <= 5:
        messages.error(request, 'Selecciona de 1 a 5 estrellas.')
    else:
        Resena.objects.update_or_create(
            escenario=cancha, usuario=request.user,
            defaults={'calificacion': calificacion, 'comentario': request.POST.get('comentario', '').strip()},
        )
        messages.success(request, '¡Gracias por tu reseña!')
    return redirect('app_escenarios:escenario_detalle', cancha.pk)


# ---------- Panel del administrador ----------

def _panel(request, **extra):
    """Lista de canchas; el formulario de crear/editar se abre como modal encima."""
    contexto = {'canchas': Escenario.objects.prefetch_related('imagenes').order_by('creado')}
    contexto.update(extra)
    return render(request, 'app_escenarios/panel.html', contexto)


@solo_admin
def panel_canchas(request):
    return _panel(request)


lista_escenarios_admin = panel_canchas


def _datos_formulario(form):
    """Separa los campos del formulario como los recibe el Administrador."""
    datos = dict(form.cleaned_data)
    servicios = datos.pop('servicios')
    return datos.pop('nombre'), datos.pop('deporte'), datos.pop('precio_hora'), datos, servicios


def _guardar_imagenes(request, escenario):
    for archivo in request.FILES.getlist('imagenes'):
        ImagenEscenario.objects.create(escenario=escenario, imagen=archivo)


@solo_admin
def crear_escenario(request):
    form = EscenarioForm(request.POST or None, initial={'precio_hora': 60000})
    if request.method == 'POST' and form.is_valid():
        nombre, tipo, precio_hora, datos, servicios = _datos_formulario(form)
        escenario = Administrador.desde_usuario(request.user).agregar_escenario(nombre, tipo, precio_hora, **datos)
        escenario.servicios.set(servicios)
        _guardar_imagenes(request, escenario)
        messages.success(request, f'Cancha "{escenario.nombre}" creada.')
        return redirect('app_escenarios:panel_canchas')
    return _panel(request, form=form, titulo='Nueva cancha')


@solo_admin
def editar_escenario(request, pk):
    cancha = get_object_or_404(Escenario, pk=pk)
    form = EscenarioForm(request.POST or None, instance=cancha)
    if request.method == 'POST' and form.is_valid():
        nombre, tipo, precio_hora, datos, servicios = _datos_formulario(form)
        Administrador.desde_usuario(request.user).editar_escenario(cancha.pk, nombre, tipo, precio_hora, **datos)
        cancha.servicios.set(servicios)
        _guardar_imagenes(request, cancha)
        borrar = request.POST.getlist('borrar_imagen')
        if borrar:
            cancha.imagenes.filter(pk__in=borrar).delete()
        messages.success(request, 'Cambios guardados.')
        return redirect('app_escenarios:panel_canchas')
    return _panel(request, form=form, cancha_editada=cancha, titulo='Editar cancha')


@solo_admin
@require_POST
def cambiar_estado_escenario(request, pk):
    cancha = get_object_or_404(Escenario, pk=pk)
    activo = cancha.cambiar_estado()
    messages.success(request, f'"{cancha.nombre}" ahora está {"activa" if activo else "inactiva"}.')
    return redirect('app_escenarios:panel_canchas')


@solo_admin
@require_POST
def eliminar_escenario(request, pk):
    cancha = get_object_or_404(Escenario, pk=pk)
    if Administrador.desde_usuario(request.user).eliminar_escenario(cancha.pk):
        messages.success(request, f'Cancha "{cancha.nombre}" eliminada.')
    return redirect('app_escenarios:panel_canchas')
