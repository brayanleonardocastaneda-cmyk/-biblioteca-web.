from abc import ABC, abstractmethod


class Pago(ABC):
    """Pago <<interface>> del diagrama: toda forma de pago debe implementar estos métodos."""

    @abstractmethod
    def procesarPago(self):
        """procesarPago(): Boolean"""

    @abstractmethod
    def generarComprobante(self):
        """generarComprobante(): String"""


class PagoEnSitio(Pago):
    """Pago en la sede: la reserva queda confirmada y se paga al llegar."""

    def __init__(self, reserva):
        self.reserva = reserva
        self.aprobado = False

    def procesarPago(self):
        self.aprobado = self.reserva.estado == 'activa'
        return self.aprobado

    def generarComprobante(self):
        return (f'Comprobante {self.reserva.codigo} - {self.reserva.escenario.nombre} - '
                f'{self.reserva.fecha:%Y-%m-%d} {", ".join(self.reserva.horas())} - '
                f'Total ${self.reserva.valor_total:,.0f} (pago en sitio)').replace(',', '.')
