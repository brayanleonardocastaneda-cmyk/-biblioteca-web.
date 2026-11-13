from django.contrib import admin
from .models import Escenario, ImagenEscenario, Resena, Servicio


class ImagenInline(admin.TabularInline):
    model = ImagenEscenario
    extra = 1


@admin.register(Escenario)
class EscenarioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'deporte', 'superficie', 'precio_hora', 'activo')
    list_filter = ('deporte', 'activo')
    inlines = [ImagenInline]


admin.site.register(Servicio)
admin.site.register(Resena)
