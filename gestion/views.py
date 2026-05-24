from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.utils import timezone
from .models import Profesional, Servicio, Sucursal, Mascota, Cita, DetalleCita, EntradaCita, Enfermedad

def obtener_servicios_por_sucursal(request):
    """
    Endpoint API que devuelve los servicios ofrecidos por una sucursal específica.
    Uso: /api/servicios/?sucursal_id=UUID_DE_LA_SUCURSAL
    """
    sucursal_id = request.GET.get('sucursal_id')
    if not sucursal_id:
        return JsonResponse({'error': 'Se requiere el parámetro sucursal_id'}, status=400)
    
    try:
        sucursal = Sucursal.objects.get(id_sucursal=sucursal_id)
        servicios = sucursal.servicios.all()
        
        data = [
            {
                'id': s.id_servicio,
                'descripcion': s.descripcion,
                'monto': s.monto,
                'divisa': s.divisa
            }
            for s in servicios
        ]
        return JsonResponse({'servicios': data}, safe=False, status=200)
    except Sucursal.DoesNotExist:
        return JsonResponse({'error': 'La sucursal no existe'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Error: {str(e)}'}, status=500)

def obtener_profesionales_por_servicio(request):
    """
    Endpoint API optimizado que devuelve los profesionales que trabajan 
    en una sucursal específica Y están capacitados para un servicio.
    Uso: /api/profesionales/?servicio_id=UUID&sucursal_id=UUID
    """
    servicio_id = request.GET.get('servicio_id')
    sucursal_id = request.GET.get('sucursal_id')
    
    if not servicio_id or not sucursal_id:
        return JsonResponse({'error': 'Se requieren servicio_id y sucursal_id'}, status=400)
    
    try:
        profesionales = Profesional.objects.filter(
            servicios__id_servicio=servicio_id,
            sucursal_id=sucursal_id
        ).select_related('cargo')
        
        data = [
            {
                'id': p.id_profesional,
                'nombre': p.nombre,
                'cargo': p.cargo.descripcion
            }
            for p in profesionales
        ]
        return JsonResponse({'profesionales': data}, safe=False, status=200)
    except Exception as e:
        return JsonResponse({'error': f'Error: {str(e)}'}, status=500)
    
def pagina_agendar(request):
    """
    Renderiza el formulario de agendamiento (GET) y procesa su creación de forma atómica (POST)
    """
    if request.method == 'POST':
        mascota_id = request.POST.get('mascota')
        sucursal_id = request.POST.get('sucursal')
        servicio_id = request.POST.get('servicio')
        profesional_id = request.POST.get('profesional')
        dia = request.POST.get('dia')
        hora = request.POST.get('hora')

        try:
            with transaction.atomic():
                mascota = Mascota.objects.get(id_mascota=mascota_id)
                sucursal = Sucursal.objects.get(id_sucursal=sucursal_id)
                profesional = Profesional.objects.get(id_profesional=profesional_id)
                servicio = Servicio.objects.get(id_servicio=servicio_id)

                ultima_cita = Cita.objects.all().order_by('-n_cita').first()
                nuevo_n_cita = (ultima_cita.n_cita + 1) if ultima_cita else 1

                cita = Cita(
                    n_cita=nuevo_n_cita,
                    mascota=mascota,
                    profesional=profesional,
                    sucursal=sucursal,
                    dia=dia,
                    hora=hora,
                    duracion_minutos=servicio.duracion_minutos,
                    monto_total=servicio.monto,
                    divisa=servicio.divisa
                )
                cita.full_clean()
                cita.save()

                detalle = DetalleCita(
                    cita=cita,
                    servicio=servicio,
                    monto_total=servicio.monto
                )
                detalle.full_clean()
                detalle.save()

            messages.success(request, f"¡Cita N° {nuevo_n_cita} agendada con éxito para {mascota.nombre}!")
            return redirect('pagina_agendar')

        except ValidationError as e:
            error_msg = " ".join(e.messages) if hasattr(e, 'messages') else str(e)
            if hasattr(e, 'message_dict'):
                error_msg = " ".join([f"{v[0]}" for v in e.message_dict.values()])
            messages.error(request, f"Restricción de negocio: {error_msg}")
            
        except Exception as e:
            messages.error(request, f"Error en el sistema: {str(e)}")

    sucursales = Sucursal.objects.all()
    mascotas = Mascota.objects.all()
    
    context = {
        'sucursales': sucursales,
        'mascotas': mascotas
    }
    return render(request, 'gestion/agendar.html', context)

def dashboard_veterinario(request):
    """
    Muestra la agenda de citas del día actual para los profesionales.
    """
    pro = Profesional.objects.all()[1]
    
    # CORRECCIÓN 2: Obtener la fecha del día de hoy respetando la zona horaria de Chile
    hoy = timezone.localdate()
    
    citas = Cita.objects.filter(
        profesional=pro,
        dia=hoy
    ).select_related('mascota', 'sucursal').order_by('hora')
    
    context = {
        'profesional': pro,
        'citas': citas,
        'hoy': hoy
    }
    return render(request, 'gestion/dashboard_vet.html', context)

def atender_cita(request, cita_id):
    """
    Controlador para atender citas. Permite modificaciones solo dentro del 
    mismo día calendario del agendamiento por motivos de seguridad y auditoría.
    """
    cita = get_object_or_404(Cita.objects.select_related('mascota__dueno', 'profesional'), id_cita=cita_id)
    entrada_existente = getattr(cita, 'entrada', None)
    
    # CORRECCIÓN 3: Ajustar la validación temporal de la ventana de edición a la zona horaria local
    hoy = timezone.localdate()
    puede_editar = (cita.dia == hoy)

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'guardar_atencion':
            if entrada_existente and not puede_editar:
                messages.error(request, "Seguridad: El plazo legal de modificación para esta consulta (mismo día) ha expirado.")
                return redirect('atender_cita', cita_id=cita_id)
                
            descripcion = request.POST.get('descripcion')
            try:
                if entrada_existente:
                    entrada_existente.descripcion = descripcion
                    entrada_existente.save()
                    messages.success(request, f"Ficha clínica de {cita.mascota.nombre} actualizada correctamente.")
                else:
                    nueva_entrada = EntradaCita(cita=cita, descripcion=descripcion)
                    nueva_entrada.save()
                    messages.success(request, f"Ficha clínica de {cita.mascota.nombre} guardada con éxito.")
                
                return redirect('atender_cita', cita_id=cita.id_cita)
                
            except Exception as e:
                messages.error(request, f"Error al procesar la ficha médica: {str(e)}")

        elif action == 'agregar_enfermedad':
            enfermedad_id = request.POST.get('enfermedad_id')
            if enfermedad_id:
                try:
                    enfermedad = Enfermedad.objects.get(id_enfermedad=enfermedad_id)
                    cita.mascota.enfermedades.add(enfermedad)
                    messages.success(request, f"Diagnóstico registrado: '{enfermedad.descripcion}' agregado al expediente.")
                except Exception as e:
                    messages.error(request, f"Error: {str(e)}")
            return redirect('atender_cita', cita_id=cita_id)

        elif action == 'quitar_enfermedad':
            enfermedad_id = request.POST.get('enfermedad_id')
            if enfermedad_id:
                try:
                    enfermedad = Enfermedad.objects.get(id_enfermedad=enfermedad_id)
                    cita.mascota.enfermedades.remove(enfermedad)
                    messages.success(request, f"Se retiró el diagnóstico '{enfermedad.descripcion}' del perfil del paciente.")
                except Exception as e:
                    messages.error(request, f"Error: {str(e)}")
            return redirect('atender_cita', cita_id=cita_id)

    enfermedades_actuales = cita.mascota.enfermedades.all()
    enfermedades_disponibles = Enfermedad.objects.exclude(id_enfermedad__in=enfermedades_actuales.values_list('id_enfermedad', flat=True))

    context = {
        'cita': cita,
        'entrada': entrada_existente,
        'puede_editar': puede_editar,
        'enfermedades_actuales': enfermedades_actuales,
        'enfermedades_disponibles': enfermedades_disponibles
    }
    return render(request, 'gestion/atender.html', context)