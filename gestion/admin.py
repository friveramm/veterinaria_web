from django.contrib import admin
from .models import Cargo, Servicio, Sucursal, Profesional, Dueno, Enfermedad, Mascota, Ficha, HorarioLaboral, Cita, DetalleCita, EntradaCita, Feedback

# Register your models here.

@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('n_servicio', 'descripcion', 'monto', 'divisa', 'duracion_minutos')
    search_fields = ('descripcion',)

@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ('n_sucursal', 'descripcion')

@admin.register(Profesional)
class ProfesionalAdmin(admin.ModelAdmin):
    list_display = ('rut', 'nombre', 'cargo', 'sucursal')
    search_fields = ('nombre', 'rut')

@admin.register(Dueno)
class DuenoAdmin(admin.ModelAdmin):
    list_display = ('rut', 'nombre', 'correo', 'fono')
    search_fields = ('nombre', 'rut', 'correo')

@admin.register(Mascota)
class MascotaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'especie', 'dueno', 'n_chip')
    search_fields = ('nombre', 'n_chip')

@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ('n_cita', 'mascota', 'profesional', 'dia', 'hora', 'hora_fin')
    list_filter = ('dia', 'sucursal')

# Registros simples para tablas secundarias
admin.site.register(Cargo)
admin.site.register(Enfermedad)
admin.site.register(Ficha)
admin.site.register(HorarioLaboral)
admin.site.register(DetalleCita)
admin.site.register(EntradaCita)
admin.site.register(Feedback)