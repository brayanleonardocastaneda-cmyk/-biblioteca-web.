from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Administrador, AuxiliarDeReservas, Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (('SportBooking', {'fields': ('rol', 'telefono')}),)
    list_display = ('username', 'first_name', 'rol', 'is_staff')


admin.site.register(Administrador)
admin.site.register(AuxiliarDeReservas)
