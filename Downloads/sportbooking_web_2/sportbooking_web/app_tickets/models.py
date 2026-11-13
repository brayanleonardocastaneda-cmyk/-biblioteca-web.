import base64
from io import BytesIO

import qrcode
from django.db import models
from app_reservas.models import Reserva


class TicketQR(models.Model):
    id_ticket = models.CharField(max_length=20, unique=True)
    reserva = models.OneToOneField(Reserva, on_delete=models.CASCADE)
    codigoQR = models.CharField(max_length=100, blank=True, default='')
    fechaEmision = models.DateTimeField(auto_now_add=True)
    estadoValidado = models.BooleanField(default=False)

    def __str__(self):
        return self.codigoQR

    @classmethod
    def emitir(cls, reserva):
        """Crea (o devuelve) el ticket de una reserva."""
        ticket, creado = cls.objects.get_or_create(reserva=reserva, defaults={'id_ticket': f'T-{reserva.pk}'})
        if creado or not ticket.codigoQR:
            ticket.generarCodigo()
        return ticket

    def generarCodigo(self):
        self.codigoQR = self.reserva.codigo
        self.save(update_fields=['codigoQR'])
        return self.codigoQR

    def imagen_qr(self):
        """Imagen PNG del QR en base64 para usarla en <img src="data:...">."""
        buffer = BytesIO()
        qrcode.make(self.codigoQR).save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode()

    def validarEntrada(self):
        """Marca el ticket como usado. Solo vale una vez y si la reserva sigue activa."""
        if self.estadoValidado or self.reserva.estado != 'activa':
            return False
        self.estadoValidado = True
        self.save(update_fields=['estadoValidado'])
        return True
