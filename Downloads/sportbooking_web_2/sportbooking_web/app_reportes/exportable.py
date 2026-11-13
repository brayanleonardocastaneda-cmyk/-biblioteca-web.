from io import BytesIO

from django.core.files.base import ContentFile

COLUMNAS = ['Código', 'Cliente', 'Cancha', 'Fecha', 'Horas', 'Estado', 'Valor']


def _filas(reservas):
    for r in reservas.select_related('cliente', 'escenario').prefetch_related('bloques'):
        yield [r.codigo, r.cliente.nombre_completo, r.escenario.nombre, r.fecha.isoformat(),
               ', '.join(r.horas()), r.get_estado_display(), float(r.valor_total)]


class Exportable:
    """Exportable del diagrama: las clases que la heredan pueden exportar reservas."""

    def exportar_excel(self, reservas):
        """Exportar_excel(Reservas: List): File"""
        from openpyxl import Workbook
        libro = Workbook()
        hoja = libro.active
        hoja.title = 'Reservas'
        hoja.append(COLUMNAS)
        for fila in _filas(reservas):
            hoja.append(fila)
        contenido = BytesIO()
        libro.save(contenido)
        return ContentFile(contenido.getvalue(), name='reservas.xlsx')

    def exportar_pdf(self, reservas):
        """Exportar_pdf(Reservas: List): File"""
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        contenido = BytesIO()
        documento = SimpleDocTemplate(contenido, pagesize=landscape(A4), title='Reporte de reservas')
        estilos = getSampleStyleSheet()
        filas = [COLUMNAS] + [fila[:-1] + [f'$ {fila[-1]:,.0f}'.replace(',', '.')] for fila in _filas(reservas)]
        tabla = Table(filas, repeatRows=1)
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#172a46')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#e6ebf2')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ]))
        documento.build([
            Paragraph('SportBooking - Reporte de reservas', estilos['Title']),
            Paragraph(self.generar_reporte(reservas), estilos['Normal']),
            Spacer(1, 12),
            tabla,
        ])
        return ContentFile(contenido.getvalue(), name='reservas.pdf')
