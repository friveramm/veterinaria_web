from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.db.models import Q, ProtectedError, Sum, Count, Avg # Para consultas complejas
from django.contrib import messages
from django.core.exceptions import ValidationError, PermissionDenied
from django.http import JsonResponse
from django.utils import timezone
from .models import Profesional, Servicio, Sucursal, Mascota, Cita, DetalleCita, EntradaCita, Enfermedad, Cargo, HorarioLaboral, Feedback
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from datetime import datetime, date

# Decoradores para RBAC
def veterinario_required(view_func):
    """ Restringe el acceso exclusivamente a usuarios con perfil profesional """
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and hasattr(request.user, 'perfil_profesional'):
            return view_func(request, *args, **kwargs)
        raise PermissionDenied # Error HTTP 403 (Prohibido)
    return _wrapped_view

def dueno_required(view_func):
    """ Restringe el acceso exclusivamente a usuarios con perfil de dueño """
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and hasattr(request.user, 'perfil_dueno'):
            return view_func(request, *args, **kwargs)
        messages.error(request, "Acceso denegado: Se requiere una cuenta de Cliente para agendar.")
        return redirect('dashboard_veterinario')
    return _wrapped_view

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
    en una sucursal específica, están capacitados para un servicio,
    Y están actualmente activos en el sistema (no han sido desvinculados).
    Uso: /api/profesionales/?servicio_id=UUID&sucursal_id=UUID
    """
    servicio_id = request.GET.get('servicio_id')
    sucursal_id = request.GET.get('sucursal_id')
    
    if not servicio_id or not sucursal_id:
        return JsonResponse({'error': 'Se requieren servicio_id y sucursal_id'}, status=400)
    
    try:
        # Verificar que no esté desvinculado user__is_active=True
        profesionales = Profesional.objects.filter(
            servicios__id_servicio=servicio_id,
            sucursal_id=sucursal_id,
            user__is_active=True
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
    
@login_required
@dueno_required
def pagina_agendar(request):
    """
    Formulario público de agendamiento. Filtra estrictamente las mascotas
    para que el cliente solo vea sus propias mascotas.
    """
    # Obtener el perfil de dueño del usuario autenticado
    dueno = request.user.perfil_dueno

    if request.method == 'POST':
        mascota_id = request.POST.get('mascota')
        sucursal_id = request.POST.get('sucursal')
        servicio_id = request.POST.get('servicio')
        profesional_id = request.POST.get('profesional')
        dia = request.POST.get('dia')
        hora = request.POST.get('hora')

        try:
            with transaction.atomic():
                # Seguridad: Validar que la mascota elegida pertenezca a este dueño
                mascota = get_object_or_404(Mascota, id_mascota=mascota_id, dueno=dueno)
                
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

    # Filtro: Traer solo las sucursales y las mascotas del dueño autenticado
    sucursales = Sucursal.objects.all()
    mascotas = Mascota.objects.filter(dueno=dueno)
    
    context = {
        'sucursales': sucursales,
        'mascotas': mascotas
    }
    return render(request, 'gestion/agendar.html', context)

@login_required
@veterinario_required
def dashboard_veterinario(request):
    """
    Intranet Médica: Carga de manera dinámica la agenda exclusiva del
    profesional logueado en el sistema.
    """
    # Se extrae el profesional mapeado directamente al usuario autenticado
    pro = request.user.perfil_profesional
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

@login_required
@veterinario_required
def atender_cita(request, cita_id):
    """
    Módulo Clínico protegido. Solo permite guardar atenciones a profesionales autorizados.
    """
    # Adicionalmente se valida que el profesional de la cita sea request.user.perfil_profesional
    cita = get_object_or_404(Cita.objects.select_related('mascota__dueno', 'profesional'), id_cita=cita_id)
    
    if cita.profesional != request.user.perfil_profesional:
        raise PermissionDenied # Bloqueo si un veterinario intenta atender la cita de otro sin permiso
        
    entrada_existente = getattr(cita, 'entrada', None)
    hoy = timezone.localdate()
    puede_editar = (cita.dia == hoy)

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'guardar_atencion':
            if entrada_existente and not puede_editar:
                messages.error(request, "Seguridad: El plazo de modificación para esta consulta ha expirado.")
                return redirect('atender_cita', cita_id=cita_id)
                
            descripcion = request.POST.get('descripcion')
            try:
                if entrada_existente:
                    entrada_existente.descripcion = descripcion
                    entrada_existente.save()
                    messages.success(request, f"Ficha clínica de {cita.mascota.nombre} actualizada.")
                else:
                    nueva_entrada = EntradaCita(cita=cita, descripcion=descripcion)
                    nueva_entrada.save()
                    messages.success(request, f"Ficha clínica de {cita.mascota.nombre} guardada.")
                
                return redirect('atender_cita', cita_id=cita.id_cita)
            except Exception as e:
                messages.error(request, f"Error al procesar la ficha médica: {str(e)}")

        elif action == 'agregar_enfermedad':
            enfermedad_id = request.POST.get('enfermedad_id')
            if enfermedad_id:
                try:
                    enfermedad = Enfermedad.objects.get(id_enfermedad=enfermedad_id)
                    cita.mascota.enfermedades.add(enfermedad)
                    messages.success(request, f"Diagnóstico registrado: '{enfermedad.descripcion}'.")
                except Exception as e:
                    messages.error(request, f"Error: {str(e)}")
            return redirect('atender_cita', cita_id=cita_id)

        elif action == 'quitar_enfermedad':
            enfermedad_id = request.POST.get('enfermedad_id')
            if enfermedad_id:
                try:
                    enfermedad = Enfermedad.objects.get(id_enfermedad=enfermedad_id)
                    cita.mascota.enfermedades.remove(enfermedad)
                    messages.success(request, f"Se retiró el diagnóstico '{enfermedad.descripcion}'.")
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

@login_required
@veterinario_required
def buscador_pacientes(request):
    """
    Motor de búsqueda de pacientes para la intranet médica.
    Devuelve HTML normal, o un JSON si la petición es asíncrona (AJAX).
    """
    query = request.GET.get('q', '').strip()
    resultados = []

    if query:
        resultados = Mascota.objects.filter(
            Q(nombre__icontains=query) | Q(dueno__rut__icontains=query)
        ).select_related('dueno')

    # Si la petición viene del JavaScript (AJAX)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = [
            {
                'id_mascota': m.id_mascota,
                'nombre': m.nombre,
                'especie': m.especie,
                'edad': m.edad,
                'dueno_nombre': m.dueno.nombre,
                'dueno_rut': m.dueno.rut
            }
            for m in resultados
        ]
        return JsonResponse({'resultados': data, 'query': query})

    # Si es una petición normal del navegador, procesa el HTML
    context = {
        'query': query,
        'resultados': resultados
    }
    return render(request, 'gestion/buscador.html', context)

@login_required
@veterinario_required
def historial_clinico(request, mascota_id):
    """
    Genera la línea de tiempo clínica de un paciente específico, extrayendo
    todas las atenciones médicas previas ordenadas cronológicamente de más reciente a más antigua.
    """
    # 1. Traer la mascota con sus datos de dueño y enfermedades crónicas
    mascota = get_object_or_404(
        Mascota.objects.select_related('dueno').prefetch_related('enfermedades'), 
        id_mascota=mascota_id
    )

    # 2. Traer solo las citas que ya tienen una ficha clínica escrita (entrada__isnull=False)
    # y ordenarlas por fecha y hora descendente (-dia, -hora)
    historial = Cita.objects.filter(
        mascota=mascota,
        entrada__isnull=False
    ).select_related('entrada', 'profesional', 'sucursal').order_by('-dia', '-hora')

    context = {
        'mascota': mascota,
        'historial': historial
    }
    return render(request, 'gestion/historial.html', context)

# Decorador de seguridad para la Jefatura
def jefe_required(view_func):
    """ Restringe el acceso únicamente a gerencia """
    def _wrapped_view(request, *args, **kwargs):
        # Solo pasa si es is_superuser
        if request.user.is_authenticated and request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return _wrapped_view

@login_required
@jefe_required
def dashboard_jefatura(request):
    """
    Dashboard de Analíticas. Ejecuta agregaciones SQL optimizadas en Postgres
    para calcular métricas del negocio en tiempo real.
    """
    hoy = timezone.localdate()
    # Tomamos desde el día 1 del mes actual, hasta el final del mes
    import calendar
    ultimo_dia = calendar.monthrange(hoy.year, hoy.month)[1]
    primer_dia_mes = hoy.replace(day=1)
    ultimo_dia_mes = hoy.replace(day=ultimo_dia)

    # 1. Agregación: Dinero de citas ya atendidas (entrada__isnull=False) en este mes
    recaudacion_mes = Cita.objects.filter(
        dia__gte=primer_dia_mes, 
        dia__lte=ultimo_dia_mes,
        entrada__isnull=False # Solo suma si el veterinario ya guardó la ficha
    ).aggregate(total=Sum('monto_total'))['total'] or 0

    # 2. Agregación: Cantidad de atenciones totales por sucursal
    metricas_sucursales = Sucursal.objects.annotate(
        num_citas=Count('citas')
    ).order_by('-num_citas')

    # 3. Agregación: Ranking de profesionales (Agenda más llena)
    ranking_profesionales = Profesional.objects.annotate(
        num_citas=Count('citas')
    ).select_related('cargo').order_by('-num_citas')

    # Catálogos para los formularios de creación rápida en el mismo dashboard
    cargos = Cargo.objects.all()
    servicios = Servicio.objects.all()
    sucursales = Sucursal.objects.all()

    # Procesar formularios rápidos enviados desde el dashboard
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'crear_cargo':
            # 1. Limpiamos los espacios en blanco accidentales
            descripcion = request.POST.get('descripcion', '').strip()
            
            # 2. Buscamos si ya existe ignorando mayúsculas y minúsculas (iexact)
            if Cargo.objects.filter(descripcion__iexact=descripcion).exists():
                messages.warning(request, f"El cargo '{descripcion}' ya se encuentra registrado en el catálogo.")
            else:
                Cargo.objects.create(descripcion=descripcion)
                messages.success(request, f"Nuevo cargo '{descripcion}' creado con éxito.")
                
            return redirect('dashboard_jefatura')
            
        elif action == 'crear_servicio':
            descripcion = request.POST.get('descripcion', '').strip()
            
            # Aplicamos la misma lógica preventiva para los servicios
            if Servicio.objects.filter(descripcion__iexact=descripcion).exists():
                messages.warning(request, f"El servicio '{descripcion}' ya existe.")
            else:
                monto = request.POST.get('monto')
                duracion = request.POST.get('duracion')
                ultimo_serv = Servicio.objects.all().order_by('-n_servicio').first()
                nuevo_n = (ultimo_serv.n_servicio + 1) if ultimo_serv else 100
                
                Servicio.objects.create(
                    n_servicio=nuevo_n, 
                    descripcion=descripcion, 
                    monto=monto, 
                    duracion_minutos=duracion
                )
                messages.success(request, f"Servicio '{descripcion}' incorporado al catálogo.")
                
            return redirect('dashboard_jefatura')
        
        elif action == 'eliminar_servicio':
            servicio_id = request.POST.get('servicio_id')
            try:
                servicio = Servicio.objects.get(id_servicio=servicio_id)
                nombre_servicio = servicio.descripcion
                # Se intenta borrar de la base de datos
                servicio.delete()
                messages.success(request, f"El servicio '{nombre_servicio}' fue eliminado del catálogo exitosamente.")
                
            except ProtectedError:
                # Si on_delete=models.PROTECT salta, se atrapa el error
                messages.error(request, "BLOQUEO DE SEGURIDAD: No puedes eliminar este servicio porque ya existen pacientes agendados o un historial médico asociado. Para dejar de ofrecerlo al público, edita la ficha de tus profesionales y desmarca esta especialidad.")
            except Exception as e:
                messages.error(request, f"Error del sistema: {str(e)}")
                
            return redirect('dashboard_jefatura')

    context = {
        'recaudacion_mes': recaudacion_mes,
        'metricas_sucursales': metricas_sucursales,
        'ranking_profesionales': ranking_profesionales,
        'cargos': cargos,
        'servicios': servicios,
        'sucursales': sucursales,
        'mes_nombre': hoy.strftime('%B %Y')
    }
    return render(request, 'gestion/dashboard_jefe.html', context)

def validar_rut_chileno(rut_bruto):
    """
    Aplica el algoritmo matemático Módulo 11 para validar si un RUT chileno es real.
    Devuelve True si es válido, False si es inválido.
    """
    rut_limpio = str(rut_bruto).replace(".", "").replace("-", "").strip().upper()
    if len(rut_limpio) < 8:
        return False
        
    cuerpo = rut_limpio[:-1]
    dv_ingresado = rut_limpio[-1]
    
    if not cuerpo.isdigit():
        return False
        
    # Algoritmo Módulo 11
    suma = 0
    multiplo = 2
    for c in reversed(cuerpo):
        suma += int(c) * multiplo
        multiplo = multiplo + 1 if multiplo < 7 else 2
        
    dv_esperado = 11 - (suma % 11)
    if dv_esperado == 11:
        dv_calculado = '0'
    elif dv_esperado == 10:
        dv_calculado = 'K'
    else:
        dv_calculado = str(dv_esperado)
        
    return dv_calculado == dv_ingresado

@login_required
@jefe_required
def administrar_profesional(request, profesional_id=None):
    profesional = None
    horarios = []
    total_horas = 0  # Variable para el contador

    if profesional_id:
        profesional = get_object_or_404(Profesional.objects.select_related('user', 'cargo', 'sucursal'), id_profesional=profesional_id)
        horarios = HorarioLaboral.objects.filter(profesional=profesional).select_related('sucursal').order_by('dia_semana', 'hora_inicio')

        # CÁLCULO DE HORAS SEMANALES: hora_fin - hora_inicio por cada bloque
        for h in horarios:
            inicio = datetime.combine(date.today(), h.hora_inicio)
            fin = datetime.combine(date.today(), h.hora_fin)
            # Diferencia en segundos dividida en 3600 para obtener horas decimales
            diferencia = (fin - inicio).total_seconds() / 3600
            total_horas += diferencia

    if request.method == 'POST':
        action = request.POST.get('action')

        # Crear o actualizar un profesional según si ya existe o no, con manejo de transacciones para garantizar la integridad de datos
        if action == 'guardar_profesional':
            rut = request.POST.get('rut')

            # Seguridad para backend: Validar que el RUT ingresado sea matemáticamente correcto antes de guardar
            if not validar_rut_chileno(rut):
                messages.error(request, "Error de validación: El RUT ingresado no es matemáticamente válido (Dígito verificador incorrecto).")
                # Si el RUT es inválido, abortamos la creación y recargamos la página
                if profesional:
                    return redirect('administrar_profesional', profesional_id=profesional.id_profesional)
                return redirect('crear_profesional')

            nombre = request.POST.get('nombre')
            cargo_id = request.POST.get('cargo')
            sucursal_id = request.POST.get('sucursal')
            servicios_ids = request.POST.getlist('servicios')

            try:
                with transaction.atomic():
                    if profesional:
                        profesional.rut = rut
                        profesional.nombre = nombre
                        profesional.cargo_id = cargo_id
                        profesional.sucursal_id = sucursal_id
                        profesional.save()
                        messages.success(request, f"Datos de {profesional.nombre} actualizados.")
                    else:
                        username = request.POST.get('username')
                        password = request.POST.get('password')
                        email = request.POST.get('email')
                        
                        user = User.objects.create_user(username=username, password=password, email=email)
                        
                        profesional = Profesional.objects.create(
                            user=user, rut=rut, nombre=nombre, cargo_id=cargo_id, sucursal_id=sucursal_id
                        )
                        messages.success(request, f"Profesional {nombre} incorporado al staff con éxito.")

                    profesional.servicios.set(servicios_ids)
                    
                return redirect('administrar_profesional', profesional_id=profesional.id_profesional)
            except Exception as e:
                messages.error(request, f"Error al procesar personal: {str(e)}")

        # Agregar un bloque de horario laboral para este profesional
        elif action == 'agregar_horario' and profesional:
            sucursal_destino_id = request.POST.get('sucursal_horario')
            dia_semana = int(request.POST.get('dia_semana'))
            hora_inicio = request.POST.get('hora_inicio')
            hora_fin = request.POST.get('hora_fin')

            choque_horario = HorarioLaboral.objects.filter(
                profesional=profesional,
                dia_semana=dia_semana,
                hora_inicio__lt=hora_fin,
                hora_fin__gt=hora_inicio,
                activo=True
            ).select_related('sucursal').first()

            if choque_horario:
                messages.error(request, f"Conflictos de agenda: El profesional ya tiene asignado un turno el mismo día en '{choque_horario.sucursal.descripcion}' dentro del rango solicitado ({choque_horario.hora_inicio} a {choque_horario.hora_fin}).")
            else:
                HorarioLaboral.objects.create(
                    profesional=profesional,
                    sucursal_id=sucursal_destino_id,
                    dia_semana=dia_semana,
                    hora_inicio=hora_inicio,
                    hora_fin=hora_fin
                )
                messages.success(request, "Bloque horario laboral añadido correctamente.")
            return redirect('administrar_profesional', profesional_id=profesional.id_profesional)

        # Eliminar un bloque de horario específico
        elif action == 'quitar_horario' and profesional:
            horario_id = request.POST.get('horario_id')
            try:
                turno = HorarioLaboral.objects.get(id_horario=horario_id, profesional=profesional)
                turno.delete()
                messages.success(request, "Turno eliminado de la agenda del profesional.")
            except HorarioLaboral.DoesNotExist:
                messages.error(request, "El turno no existe o ya fue eliminado.")
            
            return redirect('administrar_profesional', profesional_id=profesional.id_profesional)
        
        # Desvincular profesional: Revocar acceso y eliminar su agenda, pero conservar su historial médico por razones legales
        elif action == 'dar_de_baja' and profesional:
            try:
                with transaction.atomic():
                    # 1. Quitar el acceso al sistema (No podrá iniciar sesión)
                    profesional.user.is_active = False
                    profesional.user.save()
                    
                    # 2. Borramos todos sus turnos para que desaparezca de la agenda pública
                    HorarioLaboral.objects.filter(profesional=profesional).delete()
                    
                    messages.success(request, f"El profesional {profesional.nombre} ha sido desvinculado. Su acceso fue revocado y su agenda eliminada, pero su historial médico se mantiene intacto por razones legales.")
                return redirect('dashboard_jefatura')
            except Exception as e:
                messages.error(request, f"Error al desvincular: {str(e)}")

    cargos = Cargo.objects.all()
    sucursales = Sucursal.objects.all()
    servicios = Servicio.objects.all()
    
    context = {
        'profesional': profesional,
        'horarios': horarios,
        'total_horas': total_horas,
        'cargos': cargos,
        'sucursales': sucursales,
        'servicios': servicios,
        'dias_semana': HorarioLaboral.DIAS_SEMANA
    }
    return render(request, 'gestion/administrar_profesional.html', context)

@login_required
@dueno_required
def historial_cliente(request):
    """
    Portal del Cliente: Muestra el historial de atenciones de sus mascotas.
    Permite dejar una calificación única y no editable por cada atención completada.
    """
    dueno = request.user.perfil_dueno

    if request.method == 'POST':
        cita_id = request.POST.get('cita_id')
        estrellas = request.POST.get('estrellas')
        comentario = request.POST.get('comentario', '').strip()

        try:
            with transaction.atomic():
                # Validar que la cita pertenece a una mascota de este dueño
                cita = get_object_or_404(Cita, id_cita=cita_id, mascota__dueno=dueno)
                
                # Si ya tiene feedback, se bloquea la opción.
                if hasattr(cita, 'feedback'):
                    messages.warning(request, "Restricción de seguridad: Esta atención ya fue calificada y las reseñas no pueden ser modificadas.")
                else:
                    # Validar rango de estrellas
                    estrellas_int = int(estrellas)
                    if estrellas_int < 1 or estrellas_int > 5:
                        raise ValidationError("La calificación debe estar entre 1 y 5 estrellas.")

                    Feedback.objects.create(
                        cita=cita,
                        n_estrellas=estrellas_int,
                        descripcion=comentario
                    )
                    messages.success(request, f"¡Muchas gracias! Tu evaluación sobre la atención de {cita.mascota.nombre} ha sido registrada.")
            
            return redirect('historial_cliente')
            
        except ValueError:
            messages.error(request, "Error de formato en la calificación.")
        except Exception as e:
            messages.error(request, f"Error al enviar la evaluación: {str(e)}")

    # Obtener solo las citas completadas (que ya tienen una entrada médica)
    citas_completadas = Cita.objects.filter(
        mascota__dueno=dueno,
        entrada__isnull=False
    ).select_related('mascota', 'profesional', 'sucursal', 'feedback', 'entrada').order_by('-dia', '-hora')

    context = {
        'citas': citas_completadas
    }
    return render(request, 'gestion/historial_cliente.html', context)