from datetime import date

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    """Usuario del diagrama: Id_usuario (id), Nombre (first_name), Email y Contrasena."""
    ROL_CHOICES = (
        ('ADMIN', 'Administrador'),
        ('AUXILIAR', 'Auxiliar de reservas'),
        ('CLIENTE', 'Cliente'),
    )
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='CLIENTE')
    telefono = models.CharField(max_length=20, blank=True, null=True)

    @property
    def nombre_completo(self):
        return self.get_full_name() or self.email or self.username

    @staticmethod
    def iniciar_sesion(request, email, contrasena):
        """Iniciar_sesion(Email, Contrasena): boolean"""
        usuario = authenticate(request, username=email, password=contrasena)
        if usuario is None:
            return False
        login(request, usuario)
        return True

    @staticmethod
    def cerrar_sesion(request):
        """Cerrar_sesion(): void"""
        logout(request)


class Cliente(Usuario):
    """Cliente del diagrama. Es el mismo usuario (proxy) con sus propios métodos.

    Fecha_registro = date_joined, Telefono = telefono, Estado_cuenta = is_active.
    """

    class Meta:
        proxy = True

    @classmethod
    def desde_usuario(cls, usuario):
        return cls.objects.get(pk=usuario.pk)

    @property
    def fecha_registro(self):
        return self.date_joined.date()

    @property
    def estado_cuenta(self):
        return 'Activa' if self.is_active else 'Inactiva'

    @classmethod
    def registrar_usuario(cls, nombre, email, contrasena, telefono=''):
        """Registrar_usuario(Nombre, Email, Contrasena): boolean"""
        if cls.objects.filter(username=email).exists():
            return False
        cls.objects.create_user(
            username=email, email=email, password=contrasena,
            first_name=nombre, telefono=telefono, rol='CLIENTE',
        )
        return True

    def consultar_escenarios(self, fecha):
        """Consultar_escenarios(Fecha): List — canchas activas con algún horario libre ese día."""
        from app_escenarios.models import Escenario
        return [e for e in Escenario.objects.filter(activo=True)
                if any(h['disponible'] for h in e.obtener_horarios(fecha))]

    def realizar_reserva(self, escenario, fecha, hora):
        """Realizar_reserva(Escenario, Fecha, Hora): Reserva — hora puede ser una o una lista."""
        from app_reservas.models import Reserva
        horas = [hora] if isinstance(hora, str) else list(hora)
        return Reserva.crear_reserva(self, escenario, fecha, horas)

    def ver_reservas(self):
        """Ver_reservas(): List"""
        return self.reservas.select_related('escenario').prefetch_related('bloques')


class Administrador(models.Model):
    """Administrador del diagrama (perfil del usuario con is_staff)."""
    NIVELES = (('total', 'Total'), ('operativo', 'Operativo'))

    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    cargo = models.CharField(max_length=50, default='Admin')
    nivel_acceso = models.CharField(max_length=20, choices=NIVELES, default='total')
    fecha_ingreso = models.DateField(default=date.today)

    def __str__(self):
        return f'{self.usuario} ({self.cargo})'

    @property
    def id_admin(self):
        return self.pk

    @classmethod
    def desde_usuario(cls, usuario):
        administrador, _ = cls.objects.get_or_create(usuario=usuario)
        return administrador

    def agregar_escenario(self, nombre, tipo, precio_hora, **datos):
        """Agregar_escenario(Nombre, Tipo, Precio_hora): boolean — devuelve la cancha creada."""
        from app_escenarios.models import Escenario
        return Escenario.objects.create(nombre=nombre, deporte=tipo, precio_hora=precio_hora, **datos)

    def editar_escenario(self, id_escenario, nombre, tipo, precio_hora, **datos):
        """Editar_escenario(Id_escenario, Nombre, Tipo, Precio_hora): boolean"""
        from app_escenarios.models import Escenario
        return Escenario.objects.filter(pk=id_escenario).update(
            nombre=nombre, deporte=tipo, precio_hora=precio_hora, **datos) > 0

    def eliminar_escenario(self, id_escenario):
        """Eliminar_escenario(Id_escenario): boolean"""
        from app_escenarios.models import Escenario
        return Escenario.objects.filter(pk=id_escenario).delete()[0] > 0

    def consultar_todas_reservas(self):
        """Consultar_todas_reservas(): List"""
        from app_reservas.models import Reserva
        return (Reserva.objects.select_related('cliente', 'escenario').prefetch_related('bloques')
                .order_by('-fecha', '-creada'))

    def filtrar_reserva_escenario(self, id_escenario, reservas=None):
        """Filtrar_reserva_escenario(Id_escenario): List"""
        reservas = self.consultar_todas_reservas() if reservas is None else reservas
        return reservas.filter(escenario_id=id_escenario)

    def filtrar_reserva_fecha(self, fecha, reservas=None):
        """Filtrar_reserva_fecha(Fecha): List"""
        reservas = self.consultar_todas_reservas() if reservas is None else reservas
        return reservas.filter(fecha=fecha)

    def ver_detalle_reserva(self, id_reserva):
        """Ver_detalle_reserva(Id_reserva): Reserva"""
        return self.consultar_todas_reservas().filter(pk=id_reserva).first()


class AuxiliarDeReservas(models.Model):
    """AuxiliarDeReservas del diagrama: atiende reservas presenciales en la sede."""
    TURNOS = (('manana', 'Mañana'), ('tarde', 'Tarde'), ('noche', 'Noche'))

    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    turno = models.CharField(max_length=10, choices=TURNOS, default='manana')
    sede_asignada = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = 'auxiliar de reservas'
        verbose_name_plural = 'auxiliares de reservas'

    def __str__(self):
        return f'{self.usuario} ({self.get_turno_display()})'

    @property
    def id_auxiliar(self):
        return self.pk

    def consultar_escenarios_disp(self, fecha):
        """Consultar_escenarios_disp(Fecha): List"""
        from app_escenarios.models import Escenario
        return [e for e in Escenario.objects.filter(activo=True)
                if any(h['disponible'] for h in e.obtener_horarios(fecha))]

    def consultar_horarios_disp(self, fecha, id_escenario):
        """Consultar_horarios_disp(Fecha, Id_escenario): List"""
        from app_escenarios.models import Escenario
        escenario = Escenario.objects.get(pk=id_escenario)
        return [h['hora'] for h in escenario.obtener_horarios(fecha) if h['disponible']]

    def crear_reserva_presencial(self, cliente, escenario, fecha, hora):
        """Crear_reserva_presencial(Cliente, Escenario, Fecha, Hora): Reserva"""
        from app_reservas.models import Reserva
        horas = [hora] if isinstance(hora, str) else list(hora)
        return Reserva.crear_reserva(cliente, escenario, fecha, horas)

    def cancelar_reserva_cliente(self, codigo_reserva):
        """Cancelar_reserva_cliente(Codigo_reserva): boolean"""
        from app_reservas.models import Reserva
        reserva = Reserva.buscar_por_codigo(codigo_reserva)
        return bool(reserva) and reserva.cancelar_reserva()
