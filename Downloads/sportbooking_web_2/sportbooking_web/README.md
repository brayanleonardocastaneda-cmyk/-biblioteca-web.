# SportBooking (Django)

Reserva de canchas deportivas: 5 apps (`app_usuarios`, `app_escenarios`, `app_reservas`,
`app_tickets`, `app_reportes`) con modelos, vistas y plantillas según el diagrama de clases.

## Cómo correrlo

```bash
pip install -r requirements.txt
python manage.py runserver
```

`db.sqlite3` ya viene con migraciones aplicadas y datos de ejemplo. Abre http://127.0.0.1:8000/

| Rol | Correo | Contraseña |
|---|---|---|
| Administrador | admin@sportbooking.com | Admin12345 |
| Cliente | cliente@sportbooking.com | Cliente12345 |
| Auxiliar de reservas | auxiliar@sportbooking.com | Auxiliar12345 |

Si usas una base de datos nueva: `python manage.py migrate` y luego `python manage.py cargar_datos`.

## Métodos del diagrama de clases

| Clase | Dónde | Métodos |
|---|---|---|
| Usuario | `app_usuarios/models.py` | `iniciar_sesion`, `cerrar_sesion` |
| Administrador | `app_usuarios/models.py` | `agregar_escenario`, `editar_escenario`, `eliminar_escenario`, `consultar_todas_reservas`, `filtrar_reserva_escenario`, `filtrar_reserva_fecha`, `ver_detalle_reserva` |
| AuxiliarDeReservas | `app_usuarios/models.py` | `consultar_escenarios_disp`, `consultar_horarios_disp`, `crear_reserva_presencial`, `cancelar_reserva_cliente` |
| Cliente | `app_usuarios/models.py` | `registrar_usuario`, `consultar_escenarios`, `realizar_reserva`, `ver_reservas` |
| EscenarioDeportivo | `app_escenarios/models.py` (`Escenario`) | `estado_disponible`, `obtener_horarios` |
| Reserva | `app_reservas/models.py` | `consultar_reserva`, `cancelar_reserva`, `obtener_detalle` |
| Pago «interface» | `app_reservas/pagos.py` | `procesarPago`, `generarComprobante` |
| TicketQR | `app_tickets/models.py` | `generarCodigo`, `validarEntrada` |
| IServicioNotificacion | `app_tickets/notificaciones.py` | `enviar_notificacion_qr`, `enviar_confirmacion_pago` |
| ReporteReservas | `app_reportes/models.py` | `generar_reporte` |
| Exportable | `app_reportes/exportable.py` | `exportar_excel`, `exportar_pdf` |

Los correos de notificación se muestran en la consola donde corre `runserver`.
Las fotos de las canchas se suben desde el panel (botón ✏️ de cada cancha).

## Pruebas

```bash
python manage.py test
```
