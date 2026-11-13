from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect

from app_reservas.models import Reserva
from app_usuarios.permisos import solo_admin
from .models import TicketQR


@login_required
def generar_ticket(request, reserva_id):
    """Muestra el comprobante con el código QR de una reserva."""
    reserva = get_object_or_404(Reserva, pk=reserva_id)
    if reserva.cliente != request.user and not request.user.is_staff:
        return redirect('app_reservas:mis_reservas')
    return render(request, 'app_tickets/mostrar.html', {'ticket': TicketQR.emitir(reserva), 'reserva': reserva})


@solo_admin
def validar_qr_view(request):
    """GET: pantalla del validador. POST: valida el código y responde en JSON."""
    if request.method != 'POST':
        return render(request, 'app_tickets/validar.html')
    codigo = request.POST.get('codigo', '').strip().upper()
    ticket = TicketQR.objects.select_related('reserva__escenario', 'reserva__cliente').filter(codigoQR=codigo).first()
    if ticket is None:
        return JsonResponse({'valido': False, 'mensaje': 'Ticket no encontrado'})
    reserva = ticket.reserva
    ya_validado = ticket.estadoValidado
    valido = ticket.validarEntrada()
    if valido:
        mensaje = 'Acceso permitido'
    elif ya_validado:
        mensaje = 'Este ticket ya fue usado'
    else:
        mensaje = f'Reserva {reserva.get_estado_display().lower()}'
    return JsonResponse({
        'valido': valido,
        'ya_validado': ya_validado,
        'mensaje': mensaje,
        'codigo': ticket.codigoQR,
        'escenario': reserva.escenario.nombre,
        'cliente': reserva.cliente.nombre_completo,
        'fecha': reserva.fecha.strftime('%d/%m/%Y'),
        'horas': ', '.join(reserva.horas()),
    })


panel_validador = validar_qr_view
validar_ticket = validar_qr_view
