from django.urls import path
from . import views

urlpatterns = [
    # APIs
    path('api/servicios/', views.obtener_servicios_por_sucursal, name='api_servicios_por_sucursal'),
    path('api/profesionales/', views.obtener_profesionales_por_servicio, name='api_profesionales_por_servicio'),
    path('api/validar-profesional/', views.api_validar_datos_profesional, name='api_validar_profesional'),
    path('api/validar-cliente/', views.api_validar_datos_cliente, name='api_validar_cliente'),
    path('api/buscar-dueno/', views.api_buscar_dueno_por_rut, name='api_buscar_dueno'),
    
    # Público
    path('', views.index, name='index'),
    path('agendar/', views.pagina_agendar, name='pagina_agendar'),
    path('mis-atenciones/', views.historial_cliente, name='historial_cliente'),
    path('proximas-citas/', views.proximas_citas, name='proximas_citas'),
    path('registrarse/', views.registro_cliente, name='registro_cliente'),
    path('nueva-mascota/', views.agregar_mascota_cliente, name='agregar_mascota_cliente'),

    # Intranet de Veterinarios
    path('intranet/dashboard/', views.dashboard_veterinario, name='dashboard_veterinario'),
    path('intranet/atender/<uuid:cita_id>/', views.atender_cita, name='atender_cita'),
    # Intranet de Veterinarios - Buscador e historial
    path('intranet/pacientes/buscar/', views.buscador_pacientes, name='buscador_pacientes'),
    path('intranet/pacientes/<uuid:mascota_id>/historial/', views.historial_clinico, name='historial_clinico'),
    path('intranet/pacientes/nuevo/', views.agregar_mascota_veterinario, name='agregar_mascota_vet'),

    # Intranet de Jefatura / Administración
    path('intranet/jefatura/', views.dashboard_jefatura, name='dashboard_jefatura'),
    path('intranet/jefatura/profesional/nuevo/', views.administrar_profesional, name='crear_profesional'),
    path('intranet/jefatura/profesional/<uuid:profesional_id>/', views.administrar_profesional, name='administrar_profesional'),

    path('intranet/router/', views.redireccionar_por_rol, name='redireccionar_por_rol'),

    # Ruta de prueba para el error 404
    path('404/', views.error_404_view, name='error_404_test'),
]