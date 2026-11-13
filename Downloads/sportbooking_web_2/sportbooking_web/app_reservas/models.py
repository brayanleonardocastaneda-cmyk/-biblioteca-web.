from datetime import date, datetime

from django.conf import settings
from django.db import models, transaction
from app_escenarios.models import Escenario


class Reserva(models.Model):
    """Reserva del diagrama.

    Codigo_reserva = codigo, Fecha_reserva = fecha, Hora_reserva = horas(),
    Estado = estado, Fecha_creacion = creada, Valor_total = valor_total.
    """
    ESTADOS = (
        ('activa', 'Activa'), ('cancelada', 'Cancelada'), ('completada', 'Completada'),
    )
    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reservas')
    escenario = models.ForeignKey(Escenario, on_delete=models.CASCADE, related_name='reservas')
    fecha = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='activa')
    creada = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.codigo} - {self.escenario}'

    @property
    def codigo(self):
        """Codigo_reserva, ej. SB-000012."""
        return f'SB-{self.pk:06d}'

    @classmethod
    def buscar_por_codigo(cls, codigo):
        try:
            return cls.objects.filter(pk=int(codigo.strip().upper().removeprefix('SB-'))).first()
        except ValueError:
            return None

    def horas(self):
        return [b.hora.strftime('%H:%M') for b in self.bloques.all()]

    @property
    def valor_total(self):
        return self.escenario.precio_hora * len(self.bloques.all())

    @classmethod
    def crear_reserva(cls, cliente, escenario, fecha, horas):
        """Crea la reserva si todos los bloques están libres; si no, devuelve None."""
        if isinstance(fecha, str):
            fecha = date.fromisoformat(fecha)
        horas = sorted(set(horas))
        if not horas or not all(escenario.estado_disponible(fecha, h) for h in horas):
            return None
        with transaction.atomic():
            reserva = cls.objects.create(cliente=cliente, escenario=escenario, fecha=fecha)
            ReservaBloque.objects.bulk_create([
                ReservaBloque(reserva=reserva, hora=datetime.strptime(h, '%H:%M').time()) for h in horas
            ])
        return reserva

    def consultar_reserva(self):
        """Consultar_reserva(): datos de la reserva para mostrar."""
        return {
            'codigo': self.codigo, 'escenario': self.escenario.nombre, 'fecha': self.fecha,
            'horas': self.horas(), 'estado': self.get_estado_display(), 'valor_total': self.valor_total,
        }

    def puede_cancelarse(self):
        return self.estado == 'activa' and self.fecha >= date.today()

    def cancelar_reserva(self):
        """Cancelar_reserva(): pasa la reserva a cancelada (True si se pudo)."""
        if self.estado != 'activa':
            return False
        self.estado = 'cancelada'
        self.save(update_fields=['estado'])
        return True

    def completar(self):
        if self.estado != 'activa':
            return False
        self.estado = 'completada'
        self.save(update_fields=['estado'])
        return True

    def obtener_detalle(self):
        """Obtener_detalle(): String"""
        return f'{self.codigo} · {self.escenario.nombre} · {self.fecha:%Y-%m-%d} · {", ".join(self.horas())}'


class ReservaBloque(models.Model):
    """Cada hora reservada (una reserva puede tener varias horas seguidas)."""
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='bloques')
    hora = models.TimeField()

    class Meta:
        unique_together = ('reserva', 'hora')
        ordering = ['hora']
