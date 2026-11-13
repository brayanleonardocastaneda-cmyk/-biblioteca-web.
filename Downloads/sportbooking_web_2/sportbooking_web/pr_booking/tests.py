from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from app_escenarios.models import Escenario
from app_reservas.models import Reserva, ReservaBloque


class AppViewIntegrationTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.cliente = user_model.objects.create_user(
            username='cliente@example.com',
            email='cliente@example.com',
            password='Clave-segura-123',
        )
        self.admin = user_model.objects.create_user(
            username='admin@example.com',
            email='admin@example.com',
            password='Clave-segura-123',
            is_staff=True,
        )
        self.escenario = Escenario.objects.create(
            nombre='Cancha Central',
            deporte='futbol',
            superficie='sintetica',
            precio_hora=50000,
            ubicacion='Bogota',
        )

    def test_public_login_registration_and_scenario_pages_render(self):
        for name, args in (
            ('app_usuarios:login', []),
            ('app_usuarios:registro', []),
            ('app_escenarios:listar_escenarios', []),
            ('app_escenarios:escenario_detalle', [self.escenario.pk]),
            ('app_escenarios:horarios_disponibles', [self.escenario.pk]),
        ):
            response = self.client.get(reverse(name, args=args))
            self.assertEqual(response.status_code, 200, name)

    def test_customer_can_reserve_view_and_cancel(self):
        self.client.force_login(self.cliente)
        fecha = date.today() + timedelta(days=1)
        response = self.client.post(
            reverse('app_reservas:reservar', args=[self.escenario.pk]),
            {'fecha': fecha.isoformat(), 'bloques': ['10:00', '11:00']},
        )
        reserva = Reserva.objects.get(cliente=self.cliente, escenario=self.escenario)
        self.assertRedirects(
            response,
            reverse('app_reservas:reserva_confirmada', args=[reserva.pk]),
        )
        self.assertEqual(reserva.bloques.count(), 2)
        self.assertEqual(
            self.client.get(
                reverse('app_reservas:reserva_confirmada', args=[reserva.pk])
            ).status_code,
            200,
        )
        self.assertEqual(self.client.get(reverse('app_reservas:mis_reservas')).status_code, 200)

        response = self.client.post(
            reverse('app_reservas:reserva_cancelar', args=[reserva.pk])
        )
        self.assertRedirects(response, reverse('app_reservas:mis_reservas'))
        reserva.refresh_from_db()
        self.assertEqual(reserva.estado, 'cancelada')

    def test_customer_cannot_double_book_a_time_block(self):
        self.client.force_login(self.cliente)
        fecha = date.today() + timedelta(days=1)
        url = reverse('app_reservas:reservar', args=[self.escenario.pk])
        self.client.post(url, {'fecha': fecha.isoformat(), 'bloques': ['10:00']})

        response = self.client.post(url, {'fecha': fecha.isoformat(), 'bloques': ['10:00']})

        self.assertRedirects(
            response,
            reverse('app_escenarios:escenario_detalle', args=[self.escenario.pk]),
        )
        self.assertEqual(Reserva.objects.filter(fecha=fecha).count(), 1)
        self.assertEqual(ReservaBloque.objects.filter(hora='10:00').count(), 1)

    def test_admin_scenario_reservation_report_and_ticket_pages_render(self):
        self.client.force_login(self.admin)
        for name in (
            'app_escenarios:panel_canchas',
            'app_reservas:panel_reservas',
            'app_reportes:panel_reportes',
            'app_tickets:panel_validador',
        ):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200, name)

    def test_admin_can_create_scenario_and_export_reservations(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse('app_escenarios:cancha_crear'),
            {
                'nombre': 'Cancha Norte',
                'deporte': 'tenis',
                'superficie': 'natural',
                'precio_hora': '75000',
                'ubicacion': 'Medellin',
                'descripcion': '',
                'reglas': '',
                'servicios': [],
            },
        )
        self.assertRedirects(response, reverse('app_escenarios:panel_canchas'))
        self.assertTrue(Escenario.objects.filter(nombre='Cancha Norte').exists())

        response = self.client.get(reverse('app_reservas:reservas_exportar'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

    def test_ticket_validator_reports_unknown_code(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse('app_tickets:validar_ticket'),
            {'codigo': 'SB-NOEXIST'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['valido'], False)

    def test_customer_cannot_open_admin_panel(self):
        self.client.force_login(self.cliente)
        response = self.client.get(reverse('app_escenarios:panel_canchas'))
        self.assertEqual(response.status_code, 302)

    def test_reservation_ticket_can_be_validated_only_once(self):
        self.client.force_login(self.cliente)
        fecha = date.today() + timedelta(days=1)
        self.client.post(
            reverse('app_reservas:reservar', args=[self.escenario.pk]),
            {'fecha': fecha.isoformat(), 'bloques': ['09:00']},
        )
        reserva = Reserva.objects.get(cliente=self.cliente)
        self.assertEqual(reserva.valor_total, 50000)
        self.assertEqual(
            self.client.get(reverse('app_tickets:generar_ticket', args=[reserva.pk])).status_code, 200
        )

        self.client.force_login(self.admin)
        url = reverse('app_tickets:validar_ticket')
        primera = self.client.post(url, {'codigo': reserva.codigo}).json()
        segunda = self.client.post(url, {'codigo': reserva.codigo}).json()
        self.assertTrue(primera['valido'])
        self.assertFalse(segunda['valido'])
        self.assertTrue(segunda['ya_validado'])

    def test_customer_can_publish_review(self):
        self.client.force_login(self.cliente)
        url = reverse('app_escenarios:publicar_resena', args=[self.escenario.pk])
        self.client.post(url, {'calificacion': '4', 'comentario': 'Muy buena'})
        self.client.post(url, {'calificacion': '5', 'comentario': 'Excelente'})
        self.assertEqual(self.escenario.resenas.count(), 1)
        self.assertEqual(self.escenario.calificacion_promedio(), 5)

    def test_admin_can_toggle_and_delete_scenario(self):
        self.client.force_login(self.admin)
        self.client.post(reverse('app_escenarios:cambiar_estado', args=[self.escenario.pk]))
        self.escenario.refresh_from_db()
        self.assertFalse(self.escenario.activo)
        self.client.post(reverse('app_escenarios:eliminar_escenario', args=[self.escenario.pk]))
        self.assertFalse(Escenario.objects.exists())

    def test_admin_report_pages_render_with_data(self):
        Reserva.crear_reserva(self.cliente, self.escenario, date.today() + timedelta(days=2), ['18:00', '19:00'])
        self.client.force_login(self.admin)
        response = self.client.get(reverse('app_reportes:panel_reportes'))
        self.assertEqual(response.context['ingresos_totales'], 100000)
        self.assertEqual(response.context['horas_vendidas'], 2)
        for name in ('app_reportes:exportar_excel', 'app_reportes:exportar_pdf'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)

    def test_admin_calendar_view_and_sample_data(self):
        from django.core.management import call_command
        from io import StringIO
        call_command('cargar_datos', stdout=StringIO())
        self.client.force_login(self.admin)
        manana = (date.today() + timedelta(days=1)).isoformat()
        response = self.client.get(reverse('app_reservas:panel_reservas'), {'vista': 'calendario', 'fecha': manana})
        self.assertEqual(response.status_code, 200)
        fila = next(f for f in response.context['ocupacion'] if f['cancha'].nombre == 'Cancha Esmeralda Fútbol 8')
        ocupadas = [b['hora'] for b in fila['bloques'] if b['reserva']]
        self.assertEqual(ocupadas, [18, 19])
        for texto in ('Lista', 'Calendario', 'Exportar', 'Ocupación del'):
            self.assertContains(response, texto)
        reporte = self.client.get(reverse('app_reportes:panel_reportes')).context
        self.assertEqual(len(reporte['horas_pico']), 16)


class DiagramaDeClasesTests(TestCase):
    """Comprueba los métodos de cada clase del diagrama."""

    def setUp(self):
        from app_usuarios.models import Cliente
        Cliente.registrar_usuario('Ana', 'ana@example.com', 'Clave-segura-123')
        self.cliente = Cliente.objects.get(username='ana@example.com')
        self.escenario = Escenario.objects.create(
            nombre='Cancha Uno', deporte='futbol', precio_hora=40000, ubicacion='Barranquilla')
        self.manana = date.today() + timedelta(days=1)

    def test_cliente(self):
        from app_usuarios.models import Cliente
        self.assertFalse(Cliente.registrar_usuario('Ana', 'ana@example.com', 'otra-clave-123'))
        self.assertIn(self.escenario, self.cliente.consultar_escenarios(self.manana))
        reserva = self.cliente.realizar_reserva(self.escenario, self.manana, '08:00')
        self.assertEqual(list(self.cliente.ver_reservas()), [reserva])
        self.assertIsNone(self.cliente.realizar_reserva(self.escenario, self.manana, '08:00'))

    def test_escenario_y_reserva(self):
        self.assertTrue(self.escenario.estado_disponible(self.manana, '10:00'))
        reserva = self.cliente.realizar_reserva(self.escenario, self.manana, ['10:00', '11:00'])
        self.assertFalse(self.escenario.estado_disponible(self.manana, '10:00'))
        libres = [h['hora'] for h in self.escenario.obtener_horarios(self.manana) if h['disponible']]
        self.assertNotIn('11:00', libres)
        self.assertEqual(reserva.consultar_reserva()['valor_total'], 80000)
        self.assertIn('10:00, 11:00', reserva.obtener_detalle())
        self.assertTrue(reserva.cancelar_reserva())
        self.assertTrue(self.escenario.estado_disponible(self.manana, '10:00'))

    def test_administrador(self):
        from app_usuarios.models import Administrador
        admin = Administrador.desde_usuario(get_user_model().objects.create_user('jefe', password='x'))
        nueva = admin.agregar_escenario('Coliseo', 'baloncesto', 70000, ubicacion='Centro')
        self.assertTrue(admin.editar_escenario(nueva.pk, 'Coliseo 2', 'baloncesto', 75000))
        reserva = self.cliente.realizar_reserva(nueva, self.manana, '09:00')
        self.assertEqual(admin.filtrar_reserva_escenario(nueva.pk).count(), 1)
        self.assertEqual(admin.filtrar_reserva_fecha(self.manana).count(), 1)
        self.assertEqual(admin.ver_detalle_reserva(reserva.pk), reserva)
        self.assertTrue(admin.eliminar_escenario(nueva.pk))

    def test_auxiliar_de_reservas(self):
        from app_usuarios.models import AuxiliarDeReservas
        aux = AuxiliarDeReservas.objects.create(usuario=get_user_model().objects.create_user('aux', password='x'))
        self.assertIn('07:00', aux.consultar_horarios_disp(self.manana, self.escenario.pk))
        reserva = aux.crear_reserva_presencial(self.cliente, self.escenario, self.manana, '07:00')
        self.assertNotIn('07:00', aux.consultar_horarios_disp(self.manana, self.escenario.pk))
        self.assertTrue(aux.cancelar_reserva_cliente(reserva.codigo))
        self.assertFalse(aux.cancelar_reserva_cliente('SB-999999'))

    def test_pago_ticket_notificacion_y_reporte(self):
        from django.core import mail
        from app_reportes.models import ReporteReservas
        from app_reservas.pagos import PagoEnSitio
        from app_tickets.models import TicketQR
        from app_tickets.notificaciones import NotificacionCorreo

        reserva = self.cliente.realizar_reserva(self.escenario, self.manana, '15:00')
        pago = PagoEnSitio(reserva)
        self.assertTrue(pago.procesarPago())
        self.assertIn(reserva.codigo, pago.generarComprobante())
        ticket = TicketQR.emitir(reserva)
        self.assertEqual(ticket.generarCodigo(), reserva.codigo)
        self.assertTrue(ticket.validarEntrada())
        self.assertFalse(ticket.validarEntrada())
        NotificacionCorreo().enviar_notificacion_qr(ticket)
        NotificacionCorreo().enviar_confirmacion_pago(pago)
        self.assertEqual(len(mail.outbox), 2)

        reporte = ReporteReservas(id_reporte='R-1', formato_exportacion='PDF')
        self.assertIn('1 reservas', reporte.generar_reporte(Reserva.objects.all()))
        self.assertTrue(reporte.exportar_pdf(Reserva.objects.all()).read().startswith(b'%PDF'))
        self.assertTrue(reporte.exportar_excel(Reserva.objects.all()).name.endswith('.xlsx'))


class LoginTests(TestCase):
    def setUp(self):
        get_user_model().objects.create_user('ana@example.com', 'ana@example.com', 'Clave-segura-123')

    def test_login_page_like_prototype_and_login_works(self):
        response = self.client.get(reverse('app_usuarios:login'))
        for texto in ('Bienvenido de nuevo', 'Continuar con Google', '¿Olvidaste tu contraseña?', 'Créala'):
            self.assertContains(response, texto)
        response = self.client.post(reverse('app_usuarios:login'),
                                    {'email': 'ana@example.com', 'password': 'Clave-segura-123'})
        self.assertRedirects(response, reverse('app_escenarios:catalogo'))

    def test_google_button_explains_it_is_not_configured(self):
        response = self.client.get(reverse('app_usuarios:login_google'), follow=True)
        self.assertContains(response, 'Google aún no está configurado')

    def test_password_reset_sends_working_link(self):
        from django.core import mail
        import re
        self.client.post(reverse('app_usuarios:password_reset'), {'email': 'ana@example.com'})
        self.assertEqual(len(mail.outbox), 1)
        enlace = re.search(r'http://testserver(\S+)', mail.outbox[0].body).group(1)
        response = self.client.get(enlace, follow=True)
        self.assertContains(response, 'Escribe tu nueva contraseña')
        self.client.post(response.redirect_chain[-1][0] if response.redirect_chain else enlace,
                         {'new_password1': 'Nueva-clave-456', 'new_password2': 'Nueva-clave-456'})
        self.assertTrue(self.client.login(username='ana@example.com', password='Nueva-clave-456'))
