import uuid

from django.http import FileResponse
from django.shortcuts import render

from app_escenarios.models import Escenario
from app_usuarios.models import Administrador
from app_usuarios.permisos import solo_admin
from .models import ReporteReservas


@solo_admin
def panel_reportes(request):
    reservas = Administrador.desde_usuario(request.user).consultar_todas_reservas()
    canchas = list(Escenario.objects.order_by('creado'))
    return render(request, 'app_reportes/reportes.html', ReporteReservas.calcular_indicadores(reservas, canchas))


def _exportar(request, formato):
    """Guarda el reporte (ReporteReservas) y devuelve el archivo Excel o PDF."""
    reservas = Administrador.desde_usuario(request.user).consultar_todas_reservas()
    filtros = request.GET.urlencode()
    estado = request.GET.get('estado')
    if estado:
        reservas = reservas.filter(estado=estado)
    if request.GET.get('escenario'):
        reservas = reservas.filter(escenario_id=request.GET['escenario'])
    if request.GET.get('fecha'):
        reservas = reservas.filter(fecha=request.GET['fecha'])
    reporte = ReporteReservas.objects.create(
        id_reporte=f'R-{uuid.uuid4().hex[:10].upper()}', filtros_aplicados=filtros, formato_exportacion=formato)
    archivo = reporte.exportar_excel(reservas) if formato == 'EXCEL' else reporte.exportar_pdf(reservas)
    return FileResponse(archivo.open('rb'), as_attachment=True, filename=archivo.name)


@solo_admin
def exportar_excel(request):
    return _exportar(request, 'EXCEL')


@solo_admin
def exportar_pdf(request):
    return _exportar(request, 'PDF')
