from django.contrib import admin
from .models import Reserva, ReservaBloque


class BloqueInline(admin.TabularInline):
    model = ReservaBloque
    extra = 0


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'escenario', 'cliente', 'fecha', 'estado')
    list_filter = ('estado', 'escenario')
    inlines = [BloqueInline]
