from django.urls import path
from . import views

urlpatterns = [
    path('api/servicios/', views.obtener_servicios_por_sucursal, name='api_servicios_por_sucursal'),
    path('api/profesionales/', views.obtener_profesionales_por_servicio, name='api_profesionales_por_servicio'),
    path('agendar/', views.pagina_agendar, name='pagina_agendar'),
    path('intranet/dashboard/', views.dashboard_veterinario, name='dashboard_veterinario'),
    path('intranet/atender/<uuid:cita_id>/', views.atender_cita, name='atender_cita'),
]