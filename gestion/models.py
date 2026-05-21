import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
import datetime

# Create your models here.

# VALUE OBJECTS (Custom Fields para DDD)

class RutField(models.CharField):
    # Campo para formato de RUT chileno
    description = "RUT Chileno almacenado sin formato (ej: 12345678K)"

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 10
        super().__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        value = getattr(model_instance, self.attname)
        if value:
            # Limpieza: eliminar puntos, guiones y espacios, pasar K a mayúscula
            value = str(value).replace(".", "").replace("-", "").strip().upper()
            setattr(model_instance, self.attname, value)
        return value

class FonoField(models.CharField):
    # Campo para formato de teléfono chileno (+569)
    description = "Teléfono con formato internacional (ej: +56912345678)"

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 15
        super().__init__(*args, **kwargs)

# MODELOS DE LA BASE DE DATOS

class Cargo(models.Model):
    id_cargo = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=50)

    def __str__(self):
        return self.descripcion

class Servicio(models.Model):
    id_servicio = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    n_servicio = models.IntegerField(unique=True, help_text="Código correlativo del servicio")
    descripcion = models.CharField(max_length=100)
    monto = models.IntegerField()
    divisa = models.CharField(max_length=3, default="CLP")
    duracion_minutos = models.PositiveIntegerField(default=30, help_text="Duración estimada del procedimiento en minutos")

    def __str__(self):
        return f"{self.descripcion} ({self.monto} {self.divisa})"

class Sucursal(models.Model):
    id_sucursal = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    n_sucursal = models.IntegerField(unique=True)
    descripcion = models.CharField(max_length=50)
    # Una sucursal ofrece distintos servicios
    servicios = models.ManyToManyField(Servicio, related_name="sucursales", blank=True)

    def __str__(self):
        return self.descripcion

class Profesional(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil_profesional")
    id_profesional = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rut = RutField(unique=True)
    nombre = models.CharField(max_length=100)
    cargo = models.ForeignKey(Cargo, on_delete=models.PROTECT, related_name="profesionales")
    sucursal = models.ForeignKey(Sucursal, on_delete=models.PROTECT, related_name="profesionales")
    servicios = models.ManyToManyField(Servicio, related_name="profesionales", blank=True, help_text="Servicios/Especialidades que el profesional puede realizar")

    def __str__(self):
        return self.nombre

class Dueno(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil_dueno")
    id_dueno = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rut = RutField(unique=True)
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=100)
    correo = models.EmailField(max_length=50, unique=True)
    fono = FonoField()

    def __str__(self):
        return self.nombre

class Enfermedad(models.Model):
    id_enfermedad = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=100)

    def __str__(self):
        return self.descripcion

class Mascota(models.Model):
    id_mascota = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=50)
    dueno = models.ForeignKey(Dueno, on_delete=models.CASCADE, related_name="mascotas")
    n_chip = models.CharField(max_length=30, blank=True, null=True, unique=True)
    edad = models.IntegerField()
    fec_nac = models.DateField()
    especie = models.CharField(max_length=50)
    # Una mascota puede tener varias enfermedades
    enfermedades = models.ManyToManyField(Enfermedad, related_name="mascotas", blank=True)

    def __str__(self):
        return f"{self.nombre} ({self.especie})"

class Ficha(models.Model):
    id_ficha = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    n_ficha = models.IntegerField(unique=True)
    mascota = models.OneToOneField(Mascota, on_delete=models.CASCADE, related_name="ficha")

    def __str__(self):
        return f"Ficha N° {self.n_ficha} - {self.mascota.nombre}"

class HorarioLaboral(models.Model):
    DIAS_SEMANA = [
        (0, "Lunes"),
        (1, "Martes"),
        (2, "Miércoles"),
        (3, "Jueves"),
        (4, "Viernes"),
        (5, "Sábado"),
        (6, "Domingo"),
    ]

    id_horario = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profesional = models.ForeignKey(Profesional, on_delete=models.CASCADE, related_name="horarios")
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE, related_name="horarios")
    dia_semana = models.IntegerField(choices=DIAS_SEMANA)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    activo = models.BooleanField(default=True, help_text="Permite desactivar un día feriado o libre rápidamente")

    class Meta:
        # Evitar que un profesional tenga horarios duplicados el mismo día y en el mismo bloque
        unique_together = ['profesional', 'dia_semana', 'hora_inicio']

    def __str__(self):
        return f"{self.profesional.nombre} - {self.get_dia_semana_display()} ({self.hora_inicio} a {self.hora_fin})"

class Cita(models.Model):
    id_cita = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    n_cita = models.IntegerField(unique=True)
    mascota = models.ForeignKey(Mascota, on_delete=models.CASCADE, related_name="citas")
    profesional = models.ForeignKey(Profesional, on_delete=models.PROTECT, related_name="citas")
    sucursal = models.ForeignKey(Sucursal, on_delete=models.PROTECT, related_name="citas")
    
    # Para simplificar la lógica, se asume que la duración de la cita se hereda del servicio seleccionado en DetalleCita, pero se puede agregar un campo específico si se desea permitir duraciones personalizadas    
    dia = models.DateField()
    hora = models.TimeField(help_text="Hora de inicio de la cita")
    duracion_minutos = models.PositiveIntegerField(default=30, help_text="Se hereda del servicio seleccionado")
    hora_fin = models.TimeField(editable=False, null=True, blank=True, help_text="Calculado automáticamente")
    
    monto_total = models.IntegerField(default=0)
    divisa = models.CharField(max_length=3, default="CLP")

    # Cita puede tener varios servicios asociados a través de DetalleCita
    servicios = models.ManyToManyField(Servicio, through="DetalleCita", related_name="citas")

    def __str__(self):
        return f"Cita {self.n_cita} - {self.dia} {self.hora}"
    
    def clean(self):
        super().clean()
        if not self.dia or not self.hora:
            return

        # 1. Calcular automáticamente la hora_fin antes de validar
        start_datetime = datetime.datetime.combine(self.dia, self.hora)
        end_datetime = start_datetime + datetime.timedelta(minutes=self.duracion_minutos)
        self.hora_fin = end_datetime.time()

        # 2. ¿El profesional trabaja ese día en esa hora?
        dia_semana_num = self.dia.weekday() # 0 = Lunes, 6 = Domingo
        en_horario = HorarioLaboral.objects.filter(
            profesional=self.profesional,
            sucursal=self.sucursal,
            dia_semana=dia_semana_num,
            hora_inicio__lte=self.hora,
            hora_fin__gte=self.hora_fin,
            activo=True
        ).exists()

        if not en_horario:
            raise ValidationError(f"El profesional {self.profesional.nombre} no atiende en esa sucursal en el bloque solicitado ({self.hora} - {self.hora_fin}).")

        # 3. Choque de horarios
        # Dos bloques (A, B) y (C, D) chocan si: A < D y B > C
        choca_cita = Cita.objects.filter(
            profesional=self.profesional,
            dia=self.dia,
            hora__lt=self.hora_fin,
            hora_fin__gt=self.hora
        ).exclude(id_cita=self.id_cita).exists() # Excluirse a sí misma si se está editando

        if choca_cita:
            raise ValidationError(f"Agenda ocupada. El profesional ya tiene una cita agendada en ese rango de tiempo.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class DetalleCita(models.Model):
    id_detalle_cita = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cita = models.ForeignKey(Cita, on_delete=models.CASCADE, related_name="detalles")
    servicio = models.ForeignKey(Servicio, on_delete=models.PROTECT, related_name="detalles_cita")
    monto_total = models.IntegerField(help_text="Monto cobrado por este servicio específico en la cita")

    def clean(self):
            # Regla de negocio: Valida que se pueda realizar la cita en base al profesional y disponibilidad de la sucursal para el servicio solicitado
            super().clean()
            
            if self.cita and self.servicio:
                # Validar que el profesional de la cita sepa hacer el servicio
                if not self.cita.profesional.servicios.filter(id_servicio=self.servicio.id_servicio).exists():
                    raise ValidationError({
                        'servicio': f"El profesional {self.cita.profesional.nombre} no cuenta con la especialización/capacitación para realizar el servicio: '{self.servicio.descripcion}'."
                    })
                
                # Validar que la sucursal de la cita cuente con ese servicio disponible
                if not self.cita.sucursal.servicios.filter(id_servicio=self.servicio.id_servicio).exists():
                    raise ValidationError({
                        'servicio': f"La sucursal '{self.cita.sucursal.descripcion}' no ofrece el servicio solicitado en este momento."
                    })

    def save(self, *args, **kwargs):
        # Forzar para ejecutar el método clean() antes de guardar en la BD
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Detalle Cita {self.cita.n_cita} - Servicio: {self.servicio.descripcion}"

class EntradaCita(models.Model):
    # Representa las anotaciones, recetas, etc que genera el profesional en la cita
    id_entrada_cita = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cita = models.OneToOneField(Cita, on_delete=models.CASCADE, related_name="entrada")
    descripcion = models.TextField(help_text="Anotaciones de la consulta o receta médica")

    def __str__(self):
        return f"Entrada Médica Cita {self.cita.n_cita}"

class Feedback(models.Model):
    id_feedback = models.AutoField(primary_key=True)
    cita = models.OneToOneField(Cita, on_delete=models.CASCADE, related_name="feedback")
    descripcion = models.TextField(blank=True, null=True)
    n_estrellas = models.IntegerField()

    def __str__(self):
        return f"Feedback Cita {self.cita.n_cita} - {self.n_estrellas} Estrellas"