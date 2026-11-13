from datetime import date, time, timedelta

from django.core.management.base import BaseCommand

from app_escenarios.models import Escenario, Servicio
from app_reservas.models import Reserva, ReservaBloque
from app_tickets.models import TicketQR
from app_usuarios.models import Administrador, AuxiliarDeReservas, Cliente, Usuario

CANCHAS = [
    ('Cancha Esmeralda Fútbol 8', 'futbol', 'sintetica', 90000, 'Barranquilla, Cra 51B #79',
     'Cancha sintética de fútbol 8 con iluminación LED y graderías.', 'Solo guayos de caucho. Llegar 10 minutos antes.',
     ['Parqueadero', 'Duchas', 'Iluminación']),
    ('Coliseo Norte Baloncesto', 'baloncesto', 'coliseo', 75000, 'Barranquilla, Calle 98 #52',
     'Coliseo cubierto con tableros profesionales y piso de madera.', 'Uso obligatorio de tenis de suela blanca.',
     ['Parqueadero', 'Cafetería']),
    ('Club Raqueta Tenis Central', 'tenis', 'cemento', 60000, 'Barranquilla, Calle 84 #43',
     'Cancha de tenis en cemento con red reglamentaria.', 'Ropa deportiva y calzado de tenis.',
     ['Duchas', 'Cafetería']),
    ('Arena Voleibol Playa Sol', 'voleibol', 'natural', 45000, 'Barranquilla, Vía 40',
     'Cancha de voleibol playa con arena tamizada, red profesional regulable y duchas al aire libre. '
     'Perfecta para entrenamientos y torneos recreativos de fin de semana.',
     'Prohibido el ingreso con calzado. Cuidar la demarcación de la cancha.', ['Duchas', 'Cafetería']),
    ('Pádel Pro Center Cancha 1', 'padel', 'sintetica', 110000, 'Barranquilla, Calle 77 #59',
     'Cancha de pádel panorámica con cristal templado.', 'Préstamo de raquetas en recepción.',
     ['Parqueadero', 'Duchas', 'Cafetería']),
    ('Cancha Sur Fútbol 5', 'futbol', 'sintetica', 55000, 'Barranquilla, Calle 30 #8',
     'Cancha de fútbol 5 techada.', 'No se permite el ingreso de bebidas alcohólicas.', ['Parqueadero']),
]

# (cliente, cancha, días desde hoy, horas, estado)
RESERVAS = [
    ('Julián Torres', 'Club Raqueta Tenis Central', -10, [7], 'completada'),
    ('María Ruiz', 'Pádel Pro Center Cancha 1', -9, [19, 20], 'completada'),
    ('Sara Molina', 'Cancha Sur Fútbol 5', -8, [17, 18], 'completada'),
    ('Liga Empresarial SAS', 'Cancha Esmeralda Fútbol 8', -7, [20], 'completada'),
    ('Carlos Ramírez', 'Cancha Esmeralda Fútbol 8', 1, [18, 19], 'activa'),
    ('Diego Peña', 'Cancha Sur Fútbol 5', 2, [21], 'activa'),
    ('Andrea Gómez', 'Coliseo Norte Baloncesto', 2, [9, 10], 'activa'),
    ('Grupo Costa SAS', 'Arena Voleibol Playa Sol', 3, [15, 16], 'cancelada'),
]


class Command(BaseCommand):
    help = 'Carga canchas de ejemplo y usuarios de prueba (admin y cliente).'

    def handle(self, *args, **options):
        for nombre, deporte, superficie, precio, ubicacion, descripcion, reglas, servicios in CANCHAS:
            cancha, creada = Escenario.objects.get_or_create(nombre=nombre, defaults={
                'deporte': deporte, 'superficie': superficie, 'precio_hora': precio,
                'ubicacion': ubicacion, 'descripcion': descripcion, 'reglas': reglas,
            })
            if creada:
                cancha.servicios.set([Servicio.objects.get_or_create(nombre=s)[0] for s in servicios])
                self.stdout.write(f'  + {nombre}')

        if not Usuario.objects.filter(username='admin@sportbooking.com').exists():
            admin = Usuario.objects.create_superuser(
                'admin@sportbooking.com', 'admin@sportbooking.com', 'Admin12345',
                first_name='Administrador', rol='ADMIN')
            Administrador.objects.create(usuario=admin, cargo='Administrador del complejo')
        if not Usuario.objects.filter(username='cliente@sportbooking.com').exists():
            Cliente.registrar_usuario('Cliente Demo', 'cliente@sportbooking.com', 'Cliente12345')
        if not Usuario.objects.filter(username='auxiliar@sportbooking.com').exists():
            auxiliar = Usuario.objects.create_user(
                'auxiliar@sportbooking.com', 'auxiliar@sportbooking.com', 'Auxiliar12345',
                first_name='Auxiliar', rol='AUXILIAR', is_staff=True)
            AuxiliarDeReservas.objects.create(usuario=auxiliar, turno='tarde', sede_asignada='Barranquilla')

        if not Reserva.objects.exists():
            self._crear_reservas()

        self.stdout.write(self.style.SUCCESS(
            'Datos cargados.\n'
            '  Admin:   admin@sportbooking.com / Admin12345\n'
            '  Cliente: cliente@sportbooking.com / Cliente12345\n'
            '  Auxiliar: auxiliar@sportbooking.com / Auxiliar12345'))

    def _crear_reservas(self):
        for nombre, cancha, dias, horas, estado in RESERVAS:
            correo = nombre.lower().split()[0] + '@ejemplo.com'
            Cliente.registrar_usuario(nombre, correo, 'Cliente12345')
            cliente = Cliente.objects.get(username=correo)
            reserva = Reserva.objects.create(
                cliente=cliente, escenario=Escenario.objects.get(nombre=cancha),
                fecha=date.today() + timedelta(days=dias), estado=estado)
            ReservaBloque.objects.bulk_create([ReservaBloque(reserva=reserva, hora=time(h)) for h in horas])
            TicketQR.emitir(reserva)
        self.stdout.write(f'  + {len(RESERVAS)} reservas de ejemplo')
