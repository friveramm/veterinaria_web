from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction, connection # Interactuar con las secuencias de Postgres
from django.db.models import Q, ProtectedError, Sum, Count, Avg # Para consultas complejas
from django.contrib import messages
from django.core.exceptions import ValidationError, PermissionDenied
from django.http import JsonResponse
from django.utils import timezone
from .models import Ficha, Profesional, Servicio, Sucursal, Mascota, Cita, DetalleCita, EntradaCita, Enfermedad, Cargo, HorarioLaboral, Feedback, Dueno
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
                'edad': m.edad_calculada,
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
    # 1. Traer la mascota con sus datos de dueño y enfermedades
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
                # Si el RUT es inválido, se cancela la creación y recargamos la página
                if profesional:
                    return redirect('administrar_profesional', profesional_id=profesional.id_profesional)
                return redirect('crear_profesional')

            # Get a los 4 campos del nombre
            p_nombre = request.POST.get('primer_nombre', '').strip()
            s_nombre = request.POST.get('segundo_nombre', '').strip()
            p_apellido = request.POST.get('primer_apellido', '').strip()
            s_apellido = request.POST.get('segundo_apellido', '').strip()

            # Formatear para auth_user (first_name y last_name)
            first_name = f"{p_nombre} {s_nombre}".strip()
            last_name = f"{p_apellido} {s_apellido}".strip()
            
            # Formatear para tabla Profesional (nombre_completo)
            nombre_completo = f"{first_name} {last_name}".strip()

            cargo_id = request.POST.get('cargo')
            sucursal_id = request.POST.get('sucursal')
            servicios_ids = request.POST.getlist('servicios')

            try:
                with transaction.atomic():
                    if profesional:
                        # 1. Actualizar tabla Profesional
                        profesional.rut = rut
                        profesional.nombre = nombre_completo
                        profesional.cargo_id = cargo_id
                        profesional.sucursal_id = sucursal_id
                        profesional.save()

                        # 2. Actualizar también la tabla auth_user
                        profesional.user.first_name = first_name
                        profesional.user.last_name = last_name
                        profesional.user.save()

                        messages.success(request, f"Datos de {profesional.nombre} actualizados.")
                    else:
                        username = request.POST.get('username')
                        password = request.POST.get('password')
                        email = request.POST.get('email')
                        
                        # Crear el usuario en auth_user inyectando los nombres inmediatamente
                        user = User.objects.create_user(
                            username=username, 
                            password=password, 
                            email=email,
                            first_name=first_name,
                            last_name=last_name
                        )
                        
                        # Crear la ficha del Profesional
                        profesional = Profesional.objects.create(
                            user=user, 
                            rut=rut, 
                            nombre=nombre_completo, 
                            cargo_id=cargo_id, 
                            sucursal_id=sucursal_id
                        )
                        messages.success(request, f"Profesional {nombre_completo} incorporado al staff con éxito.")

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
                    
                    # 2. Borrar todos sus turnos para que desaparezca de la agenda pública
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

def index(request):
    """
    Página de inicio pública de la veterinaria.
    Muestra información de la clínica, servicios y reseñas.
    """
    servicios_disponibles = Servicio.objects.all().order_by('descripcion')
    
    # Traer los últimos 3 feedbacks positivos (4 o 5 estrellas) para mostrarlos
    mejores_feedbacks = Feedback.objects.filter(
        n_estrellas__gte=4
    ).select_related('cita__mascota__dueno').order_by('-id_feedback')[:3]
    
    # Calcular el promedio general de todas las reseñas de la plataforma
    promedio_calculado = Feedback.objects.aggregate(promedio_general=Avg('n_estrellas'))['promedio_general']
    # Si hay reseñas, redondear a 1 decimal. Si no hay, mandar 0.0
    promedio_general = round(promedio_calculado, 1) if promedio_calculado else 0.0
    
    context = {
        'servicios': servicios_disponibles,
        'feedbacks': mejores_feedbacks,
        'promedio_general': promedio_general, # Promedio al HTML
    }
    return render(request, 'gestion/index.html', context)

@login_required
def redireccionar_por_rol(request):
    """
    Vista intermedia (Router) que redirige al usuario a su panel correspondiente
    según su rol/perfil asignado tras iniciar sesión de forma exitosa.
    """
    # 1. Si es superuser
    if request.user.is_superuser:
        return redirect('dashboard_jefatura')
        
    # 2. Si es veterinario
    elif hasattr(request.user, 'perfil_profesional'):
        return redirect('dashboard_veterinario')
        
    # 3. Si es cliente
    elif hasattr(request.user, 'perfil_dueno'):
        return redirect('historial_cliente')
        
    # 4. Si es usuario común
    else:
        return redirect('index')
    
@login_required
@jefe_required
def api_validar_datos_profesional(request):
    """
    Endpoint AJAX para validar en tiempo real si el username o el RUT 
    ya existen antes de enviar el formulario.
    """
    username = request.GET.get('username', '').strip()
    rut = request.GET.get('rut', '').strip()
    exclude_id = request.GET.get('exclude_id', '').strip()

    data = {
        'username_usado': False,
        'rut_usado': False,
        'rut_dueno': ''
    }

    # 1. Validar Username
    if username:
        if User.objects.filter(username__iexact=username).exists():
            data['username_usado'] = True

    # 2. Validar RUT
    if rut:
        # Limpiar el RUT usando el mismo estándar del modelo
        rut_limpio = rut.replace(".", "").replace("-", "").strip().upper()
        query = Profesional.objects.filter(rut=rut_limpio)
        
        # Si está editando a un profesional, se excluye su propio ID para que no salte error con su propio RUT
        if exclude_id:
            query = query.exclude(id_profesional=exclude_id)
        
        prof_existente = query.first()
        if prof_existente:
            data['rut_usado'] = True
            data['rut_dueno'] = prof_existente.nombre

    return JsonResponse(data)

@login_required
@veterinario_required
def api_buscar_dueno_por_rut(request):
    """
    Endpoint AJAX Autocompletado: Busca clientes cuyo RUT contenga 
    los números que el veterinario está tecleando.
    """
    rut_bruto = request.GET.get('rut', '')
    rut_limpio = rut_bruto.replace(".", "").replace("-", "").strip().upper()
    
    # Si tiene menos de 6 números, no buscamos para no saturar la BD
    if len(rut_limpio) < 6:
        return JsonResponse({'resultados': []})
        
    # Filtrar dueños que contengan esos números en su RUT (Máximo 5 resultados)
    duenos = Dueno.objects.filter(rut__icontains=rut_limpio)[:5]
    
    data = [
        {
            'rut_bd': d.rut,
            'nombre': d.nombre
        }
        for d in duenos
    ]
    
    return JsonResponse({'resultados': data})

@login_required
@dueno_required
def proximas_citas(request):
    """
    Portal del Cliente: Muestra las citas agendadas desde el día de hoy en adelante.
    """
    dueno = request.user.perfil_dueno
    hoy = timezone.localdate()

    # Agregar prefetch_related('servicios') para optimizar la carga de los servicios agendados
    citas_futuras = Cita.objects.filter(
        mascota__dueno=dueno,
        dia__gte=hoy
    ).select_related('mascota', 'profesional', 'sucursal', 'entrada').prefetch_related('servicios').order_by('dia', 'hora')

    context = {
        'citas': citas_futuras,
        'hoy': hoy
    }
    return render(request, 'gestion/proximas_citas.html', context)

def registro_cliente(request):
    """
    Portal Público: Permite a un nuevo cliente crear su cuenta.
    Poblar las tablas auth_user y Dueno simultáneamente.
    """
    # Si ya está logueado, mandar a su panel
    if request.user.is_authenticated:
        return redirect('redireccionar_por_rol')

    if request.method == 'POST':
        rut = request.POST.get('rut')
        
        # Validación matemática del RUT
        if not validar_rut_chileno(rut):
            messages.error(request, "El RUT ingresado no es válido.")
            return redirect('registro_cliente')

        username = request.POST.get('username').strip()
        email = request.POST.get('email').strip()
        password = request.POST.get('password')
        direccion = request.POST.get('direccion').strip()
        fono = request.POST.get('fono').strip()

        # Atrapar los 4 campos del nombre
        p_nombre = request.POST.get('primer_nombre', '').strip()
        s_nombre = request.POST.get('segundo_nombre', '').strip()
        p_apellido = request.POST.get('primer_apellido', '').strip()
        s_apellido = request.POST.get('segundo_apellido', '').strip()

        # Validación de seguridad: El primer nombre y el primer apellido son obligatorios 
        # para evitar registros con datos insuficientes
        if not p_nombre or not p_apellido:
            messages.error(request, "Error de seguridad: El primer nombre y el primer apellido son obligatorios.")
            return redirect('registro_cliente')

        # Formatear nombres
        first_name = f"{p_nombre} {s_nombre}".strip()
        last_name = f"{p_apellido} {s_apellido}".strip()
        nombre_completo = f"{first_name} {last_name}".strip()

        try:
            with transaction.atomic():
                # 1. Validaciones de existencia (Usuario y Correo)
                if User.objects.filter(username__iexact=username).exists():
                    messages.error(request, "El nombre de usuario ya está en uso. Elige otro.")
                    return redirect('registro_cliente')
                
                if User.objects.filter(email__iexact=email).exists() or Dueno.objects.filter(correo__iexact=email).exists():
                    messages.error(request, "Este correo electrónico ya está registrado en el sistema.")
                    return redirect('registro_cliente')

                # 2. Formatear RUT para verificar si existe en la BD
                rut_limpio = str(rut).replace(".", "").replace("-", "").strip().upper()
                if Dueno.objects.filter(rut=rut_limpio).exists():
                    messages.error(request, "Este RUT ya se encuentra registrado. Si olvidaste tu contraseña, contacta a la clínica.")
                    return redirect('registro_cliente')

                # 3. Crear credenciales en auth_user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )

                # 4. Crear ficha en la tabla Dueno
                Dueno.objects.create(
                    user=user,
                    rut=rut,
                    nombre=nombre_completo,
                    direccion=direccion,
                    correo=email,
                    fono=fono
                )
            
            # Éxito:
            context = {
                'registro_exitoso': True,
                'nombre_usuario': p_nombre
            }
            return render(request, 'gestion/registro.html', context)

        except Exception as e:
            messages.error(request, f"Error al registrar la cuenta: {str(e)}")
            return redirect('registro_cliente')

    return render(request, 'gestion/registro.html')

def api_validar_datos_cliente(request):
    """
    Endpoint AJAX para validar en tiempo real si el username, 
    email o RUT ya existen en el registro público de clientes.
    """
    username = request.GET.get('username', '').strip()
    rut = request.GET.get('rut', '').strip()
    email = request.GET.get('email', '').strip()

    data = {
        'username_usado': False,
        'rut_usado': False,
        'email_usado': False
    }

    if username and User.objects.filter(username__iexact=username).exists():
        data['username_usado'] = True

    if email and (User.objects.filter(email__iexact=email).exists() or Dueno.objects.filter(correo__iexact=email).exists()):
        data['email_usado'] = True

    if rut:
        rut_limpio = rut.replace(".", "").replace("-", "").strip().upper()
        if Dueno.objects.filter(rut=rut_limpio).exists():
            data['rut_usado'] = True

    return JsonResponse(data)

def obtener_siguiente_n_ficha():
    """
    Consulta de forma atómica el siguiente número correlativo disponible
    en la secuencia nativa de PostgreSQL.
    """
    with connection.cursor() as cursor:
        cursor.execute("SELECT nextval('gestion_ficha_n_ficha_seq')")
        return cursor.fetchone()[0]

@login_required
@dueno_required
def agregar_mascota_cliente(request):
    """
    Portal Cliente: Permite al dueño registrar una nueva mascota.
    """
    dueno = request.user.perfil_dueno

    if request.method == 'POST':
        nombre = request.POST.get('nombre').strip()
        especie = request.POST.get('especie').strip()
        fec_nac = request.POST.get('fec_nac')
        n_chip = request.POST.get('n_chip', '').strip() or None

        try:
            with transaction.atomic():
                # 1. Crear la Mascota en la BD
                mascota = Mascota.objects.create(
                    nombre=nombre,
                    dueno=dueno,
                    especie=especie,
                    fec_nac=fec_nac,
                    n_chip=n_chip
                )
                
                # 2. Generar su Ficha con un número correlativo seguro y atómico
                nuevo_n_ficha = obtener_siguiente_n_ficha()
                
                Ficha.objects.create(n_ficha=nuevo_n_ficha, mascota=mascota)
                
            messages.success(request, f"¡{nombre} ha sido registrado/a con éxito! Su Ficha Clínica es la N° {nuevo_n_ficha}.")
            return redirect('historial_cliente')

        except Exception as e:
            messages.error(request, f"Error crítico al registrar mascota: {str(e)}")

    return render(request, 'gestion/agregar_mascota_cliente.html')


@login_required
@veterinario_required
def agregar_mascota_veterinario(request):
    """
    Intranet Médica: Permite al profesional registrar un paciente nuevo.
    Requiere validar el RUT del dueño primero.
    """
    if request.method == 'POST':
        rut_bruto = request.POST.get('rut_dueno', '')
        rut_limpio = str(rut_bruto).replace(".", "").replace("-", "").strip().upper()
        
        try:
            # Buscar al dueño por RUT
            dueno = Dueno.objects.get(rut=rut_limpio)
        except Dueno.DoesNotExist:
            messages.error(request, "El RUT ingresado no corresponde a ningún cliente registrado en el sistema. El dueño debe crear su cuenta primero.")
            return redirect('agregar_mascota_vet')

        nombre = request.POST.get('nombre').strip()
        especie = request.POST.get('especie').strip()
        fec_nac = request.POST.get('fec_nac')
        n_chip = request.POST.get('n_chip', '').strip() or None

        try:
            with transaction.atomic():
                mascota = Mascota.objects.create(
                    nombre=nombre,
                    dueno=dueno,
                    especie=especie,
                    fec_nac=fec_nac,
                    n_chip=n_chip
                )
                
                # 2. Generar su Ficha con un número correlativo seguro y atómico
                nuevo_n_ficha = obtener_siguiente_n_ficha()
                Ficha.objects.create(n_ficha=nuevo_n_ficha, mascota=mascota)
                
            messages.success(request, f"Paciente {nombre} agregado con éxito a la cuenta de {dueno.nombre}.")
            return redirect('buscador_pacientes') # Redirige al buscador médico

        except Exception as e:
            messages.error(request, f"Error del sistema: {str(e)}")

    return render(request, 'gestion/agregar_mascota_vet.html')

def error_404_view(request, exception=None):
    """
    Manejador manual y oficial para el error 404 (Página no encontrada).
    Renderiza la plantilla personalizada dentro de la app 'gestion'.
    """
    return render(request, 'gestion/404.html', status=404)