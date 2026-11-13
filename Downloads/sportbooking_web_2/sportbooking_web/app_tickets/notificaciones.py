from abc import ABC, abstractmethod

from django.core.mail import send_mail


class IServicioNotificacion(ABC):
    """IServicioNotificacion del diagrama."""

    @abstractmethod
    def enviar_notificacion_qr(self, ticket):
        """enviar_notificacion_qr(ticket: TicketQR): void"""

    @abstractmethod
    def enviar_confirmacion_pago(self, pago):
        """enviar_confirmacion_pago(pago: Pago): void"""


class NotificacionCorreo(IServicioNotificacion):
    """Envía los avisos por correo (en desarrollo se ven en la consola de runserver)."""

    remitente = 'SportBooking <no-responder@sportbooking.com>'

    def enviar_notificacion_qr(self, ticket):
        reserva = ticket.reserva
        send_mail(
            f'Tu ticket {ticket.codigoQR}',
            f'Hola {reserva.cliente.nombre_completo}, presenta el código {ticket.codigoQR} '
            f'en la entrada de {reserva.escenario.nombre} el {reserva.fecha:%Y-%m-%d} '
            f'a las {", ".join(reserva.horas())}.',
            self.remitente, [reserva.cliente.email], fail_silently=True,
        )

    def enviar_confirmacion_pago(self, pago):
        send_mail('Confirmación de tu reserva', pago.generarComprobante(),
                  self.remitente, [pago.reserva.cliente.email], fail_silently=True)
