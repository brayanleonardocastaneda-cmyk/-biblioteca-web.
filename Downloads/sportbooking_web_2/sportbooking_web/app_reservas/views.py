from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from app_escenarios.models import Escenario
from app_reportes.views import exportar_excel
from app_tickets.models import TicketQR
from app_tickets.notificaciones import NotificacionCorreo
from app_usuarios.models import Administrador, Cliente
from app_usuarios.permisos import solo_admin
from .models import Reserva
from .pagos import PagoEnSitio


@solo_admin
def panel_reservas(request):
    """Panel del administrador: usa los métodos de consulta y filtro del Administrador."""
    administrador = Administrador.desde_usuario(request.user)
    filtros = {
        'estado': request.GET.get('estado', ''),
        'escenario': request.GET.get('escenario', ''),
        'fecha': request.GET.get('fecha', ''),
    }
    reservas = administrador.consultar_todas_reservas()
    if filtros['estado']:
        reservas = reservas.filter(estado=filtros['estado'])
    if filtros['escenario']:
        reservas = administrador.filtrar_reserva_escenario(filtros['escenario'], reservas)
    if filtros['fecha']:
        reservas = administrador.filtrar_reserva_fecha(filtros['fecha'], reservas)

    vista = request.GET.get('vista', 'lista')
    canchas = Escenario.objects.order_by('creado')
    contexto = {
        'reservas': reservas,
        'filtros': filtros,
        'estados': Reserva.ESTADOS,
        'canchas': canchas,
        'vista': vista,
        'query': request.GET.urlencode(),
    }
    if vista == 'calendario':
        try:
            dia = date.fromisoformat(filtros['fecha'])
        except ValueError:
            dia = date.today()
        if filtros['escenario']:
            canchas = canchas.filter(pk=filtros['escenario'])
        contexto.update({
            'dia': dia,
            'ocupacion': [{'cancha': c, 'bloques': c.ocupacion_dia(dia)} for c in canchas],
        })
    return render(request, 'app_reservas/admin_lista.html', contexto)


lista_reservas_admin = panel_reservas
reservas_exportar = exportar_excel


@login_required
def reservar(request, cancha_id):
    """El cliente reserva: Realizar_reserva -> Pago -> TicketQR -> notificaciones."""
    cancha = get_object_or_404(Escenario, pk=cancha_id, activo=True)
    if request.method != 'POST':
        return redirect('app_escenarios:escenario_detalle', cancha.pk)
    cliente = Cliente.desde_usuario(request.user)
    try:
        reserva = cliente.realizar_reserva(cancha, request.POST.get('fecha', ''), request.POST.getlist('bloques'))
    except ValueError:
        reserva = None
    if reserva is None:
        messages.error(request, 'Elige al menos un horario disponible. Puede que alguien lo haya reservado antes.')
        return redirect('app_escenarios:escenario_detalle', cancha.pk)

    pago = PagoEnSitio(reserva)
    pago.procesarPago()
    ticket = TicketQR.emitir(reserva)
    notificacion = NotificacionCorreo()
    notificacion.enviar_confirmacion_pago(pago)
    notificacion.enviar_notificacion_qr(ticket)
    return redirect('app_reservas:reserva_confirmada', reserva.pk)


crear_reserva = reservar


@login_required
def reserva_confirmada(request, pk):
    reserva = get_object_or_404(Reserva, pk=pk, cliente=request.user)
    return render(request, 'app_reservas/confirmacion.html', {
        'reserva': reserva,
        'ticket': TicketQR.emitir(reserva),
        'comprobante': PagoEnSitio(reserva).generarComprobante(),
    })


@login_required
def mis_reservas(request):
    reservas = Cliente.desde_usuario(request.user).ver_reservas().select_related('ticketqr').order_by('-fecha', '-creada')
    return render(request, 'app_reservas/mis_reservas.html', {
        'proximas': [r for r in reservas if r.puede_cancelarse()],
        'historial': [r for r in reservas if not r.puede_cancelarse()],
    })


@login_required
@require_POST
def reserva_cancelar(request, pk):
    reserva = get_object_or_404(Reserva, pk=pk, cliente=request.user)
    if reserva.puede_cancelarse() and reserva.cancelar_reserva():
        messages.success(request, f'Reserva {reserva.codigo} cancelada.')
    else:
        messages.error(request, 'Esta reserva ya no se puede cancelar.')
    return redirect('app_reservas:mis_reservas')


cancelar_reserva = reserva_cancelar


@solo_admin
@require_POST
def completar_reserva(request, pk):
    reserva = get_object_or_404(Reserva, pk=pk)
    if reserva.completar():
        messages.success(request, f'Reserva {reserva.codigo} completada.')
    siguiente = request.POST.get('next', '')
    if siguiente and url_has_allowed_host_and_scheme(siguiente, {request.get_host()}):
        return redirect(siguiente)
    return redirect('app_reservas:panel_reservas')


@login_required
def detalle_reserva(request, pk):
    if request.user.is_staff:
        reserva = Administrador.desde_usuario(request.user).ver_detalle_reserva(pk)
    else:
        reserva = Reserva.objects.filter(pk=pk, cliente=request.user).first()
    if reserva is None:
        return redirect('app_reservas:mis_reservas')
    return render(request, 'app_reservas/detalle.html', {
        'reserva': reserva, 'ticket': TicketQR.emitir(reserva), 'detalle': reserva.obtener_detalle(),
    })
