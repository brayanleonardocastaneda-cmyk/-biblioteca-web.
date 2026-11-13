from datetime import date, datetime, time

from django.db import models
from django.db.models import Avg, Count
from django.utils import timezone

# Bloques de una hora que se pueden reservar: 07:00 a 22:00
HORARIOS = [time(h) for h in range(7, 23)]


class Servicio(models.Model):
    nombre = models.CharField(max_length=40, unique=True)

    def __str__(self):
        return self.nombre


class Escenario(models.Model):
    """EscenarioDeportivo del diagrama de clases."""
    DEPORTES = (
        ('futbol', 'Fútbol'), ('baloncesto', 'Baloncesto'), ('tenis', 'Tenis'),
        ('voleibol', 'Voleibol'), ('padel', 'Pádel'),
    )
    SUPERFICIES = (
        ('sintetica', 'Sintética'), ('natural', 'Natural'),
        ('cemento', 'Cemento'), ('coliseo', 'Coliseo'),
    )

    nombre = models.CharField(max_length=120)
    deporte = models.CharField(max_length=20, choices=DEPORTES)
    superficie = models.CharField(max_length=20, choices=SUPERFICIES, default='sintetica')
    precio_hora = models.DecimalField(max_digits=10, decimal_places=0)
    ubicacion = models.CharField(max_length=160)
    descripcion = models.TextField(blank=True)
    reglas = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    servicios = models.ManyToManyField(Servicio, blank=True, related_name='escenarios')
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creado']

    def __str__(self):
        return self.nombre

    def imagen_principal(self):
        primera = self.imagenes.first()
        return primera.imagen.url if primera else None

    def horas_ocupadas(self, fecha):
        """Horas ya reservadas (reservas activas) para una fecha."""
        return set(
            self.reservas.filter(fecha=fecha, estado='activa')
            .values_list('bloques__hora', flat=True)
        )

    def estado_disponible(self, fecha, hora):
        """True si el bloque fecha/hora se puede reservar."""
        if isinstance(fecha, str):
            fecha = date.fromisoformat(fecha)
        if isinstance(hora, str):
            hora = datetime.strptime(hora, '%H:%M').time()
        if not self.activo or hora not in HORARIOS:
            return False
        ahora = timezone.localtime()
        if fecha < ahora.date() or (fecha == ahora.date() and hora <= ahora.time()):
            return False
        return hora not in self.horas_ocupadas(fecha)

    def obtener_horarios(self, fecha):
        """Lista de bloques del día con su disponibilidad (para el template)."""
        ocupadas = self.horas_ocupadas(fecha)
        ahora = timezone.localtime()
        horarios = []
        for hora in HORARIOS:
            pasada = fecha < ahora.date() or (fecha == ahora.date() and hora <= ahora.time())
            horarios.append({
                'hora': hora.strftime('%H:%M'),
                'disponible': self.activo and not pasada and hora not in ocupadas,
            })
        return horarios

    def ocupacion_dia(self, fecha):
        """Bloques del día con la reserva que los ocupa (vista Calendario del panel)."""
        ocupados = {}
        for reserva in self.reservas.filter(fecha=fecha).exclude(estado='cancelada').prefetch_related('bloques'):
            for bloque in reserva.bloques.all():
                ocupados[bloque.hora] = reserva
        return [{'hora': h.hour, 'reserva': ocupados.get(h)} for h in HORARIOS]

    def calificacion_promedio(self):
        promedio = self.resenas.aggregate(p=Avg('calificacion'))['p']
        return round(promedio or 0, 1)

    def resumen_calificaciones(self):
        """Cantidad y porcentaje de reseñas por número de estrellas (5 a 1)."""
        conteo = dict(self.resenas.values_list('calificacion').annotate(c=Count('id')))
        total = sum(conteo.values())
        return [
            {'estrellas': e, 'cantidad': conteo.get(e, 0),
             'porcentaje': round(conteo.get(e, 0) * 100 / total) if total else 0}
            for e in range(5, 0, -1)
        ]

    def cambiar_estado(self):
        """Activa o desactiva la cancha (botón de encendido del panel)."""
        self.activo = not self.activo
        self.save(update_fields=['activo'])
        return self.activo


class ImagenEscenario(models.Model):
    escenario = models.ForeignKey(Escenario, on_delete=models.CASCADE, related_name='imagenes')
    imagen = models.ImageField(upload_to='escenarios/')


class Resena(models.Model):
    escenario = models.ForeignKey(Escenario, on_delete=models.CASCADE, related_name='resenas')
    usuario = models.ForeignKey('app_usuarios.Usuario', on_delete=models.CASCADE)
    calificacion = models.PositiveSmallIntegerField()
    comentario = models.TextField(blank=True)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creada']
        unique_together = ('escenario', 'usuario')

    def estrellas(self):
        return '★' * self.calificacion + '☆' * (5 - self.calificacion)


# Nombre usado en el diagrama de clases.
EscenarioDeportivo = Escenario
