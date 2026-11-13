from django.db import models

from .exportable import Exportable


class ReporteReservas(Exportable, models.Model):
    id_reporte = models.CharField(max_length=20, unique=True)
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    filtros_aplicados = models.CharField(max_length=255, blank=True)
    formato_exportacion = models.CharField(max_length=10)  # PDF, EXCEL

    def __str__(self):
        return self.id_reporte

    def generar_reporte(self, reservas):
        """Generar_reporte(Reservas: List): String — resumen en texto."""
        datos = self.calcular_indicadores(reservas, [])
        return (f'{len(reservas)} reservas · {datos["horas_vendidas"]} horas vendidas · '
                f'ingresos $ {datos["ingresos_totales"]:,.0f}').replace(',', '.')

    @staticmethod
    def calcular_indicadores(reservas, canchas):
        """Calcula los indicadores del panel de reportes.

        reservas: queryset de reservas (las canceladas no cuentan).
        canchas: canchas que aparecen en la gráfica de ingresos.
        """
        from app_escenarios.models import HORARIOS

        validas = list(reservas.exclude(estado='cancelada').select_related('escenario').prefetch_related('bloques'))
        ingresos = 0
        horas_vendidas = 0
        por_cancha = {c.pk: 0 for c in canchas}
        por_hora = {h: 0 for h in HORARIOS}
        for reserva in validas:
            bloques = list(reserva.bloques.all())
            valor = reserva.escenario.precio_hora * len(bloques)
            ingresos += valor
            horas_vendidas += len(bloques)
            por_cancha[reserva.escenario_id] = por_cancha.get(reserva.escenario_id, 0) + float(valor)
            for bloque in bloques:
                if bloque.hora in por_hora:
                    por_hora[bloque.hora] += 1

        # Ocupación: horas vendidas frente a los bloques ofrecidos en los días con reservas
        dias = len({r.fecha for r in validas})
        capacidad = len(canchas) * len(HORARIOS) * dias
        ocupacion = round(horas_vendidas * 100 / capacidad) if capacidad else 0

        return {
            'ingresos_totales': ingresos,
            'horas_vendidas': horas_vendidas,
            'ocupacion': ocupacion,
            'horas_pico': [{'hora': h.strftime('%H:%M'), 'reservas': n} for h, n in por_hora.items()],
            'ingresos_por_cancha': [{'nombre': c.nombre, 'ingresos': por_cancha.get(c.pk, 0)} for c in canchas],
        }
