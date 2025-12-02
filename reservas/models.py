import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from habitaciones.models import TipoHabitacion, Habitacion
from administracion.models import Servicio, Plan, Promocion
from decimal import Decimal
from django.utils import timezone


class Reserva(models.Model):
    ESTADOS_RESERVA = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('activa', 'Activa'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    ]

    METODOS_PAGO = [
        ('efectivo', 'Efectivo'),
        ('debito', 'Débito'),
        ('credito', 'Crédito'),
        ('mercadopago', 'MercadoPago'),
        ('paypal', 'PayPal'),
        ('crypto', 'Criptomonedas'),
        ('transferencia', 'Transferencia Bancaria'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    tipo_habitacion = models.ForeignKey(TipoHabitacion, on_delete=models.CASCADE, related_name='reservas')
    habitacion_asignada = models.ForeignKey(Habitacion, on_delete=models.SET_NULL, null=True, blank=True, 
                                          help_text="Habitación específica asignada al hacer check-in")
    cantidad_habitaciones = models.PositiveIntegerField(default=1, help_text="Cantidad de habitaciones reservadas")
    servicios = models.ManyToManyField(Servicio, blank=True)

    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, blank=True)
    promocion = models.ForeignKey(Promocion, on_delete=models.SET_NULL, null=True, blank=True)

    fecha_reserva = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS_RESERVA, default='pendiente')
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO, blank=True, null=True)
    token = models.CharField(max_length=64, default=uuid.uuid4, editable=False, unique=True)
    codigo_checkin = models.CharField(max_length=10, null=True, blank=True, help_text="Código de seguridad para realizar el check-in")
    monto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    check_in = models.DateField(null=True, blank=True)
    check_out = models.DateField(null=True, blank=True)
    cantidad_huespedes = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['-fecha_reserva']
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"

    def __str__(self):
        detalle = f"Reserva de {self.usuario.username} - {self.tipo_habitacion.nombre}"
        if self.cantidad_habitaciones > 1:
            detalle += f" (x{self.cantidad_habitaciones})"
        if self.plan:
            detalle += f" - Plan: {self.plan.nombre}"
        if self.promocion:
            detalle += f" - Promoción: {self.promocion.nombre}"
        return detalle

    def save(self, *args, **kwargs):
        """Override save para gestionar el stock automáticamente"""
        # Si es una nueva reserva y está confirmada, reservar stock
        if not self.pk and self.estado == 'confirmada':
            if not self.tipo_habitacion.reservar_stock(self.cantidad_habitaciones):
                raise ValidationError(f"No hay suficiente stock disponible para {self.tipo_habitacion.nombre}")
        
        # Si se está cambiando el estado
        elif self.pk:
            old_reserva = Reserva.objects.get(pk=self.pk)
            
            # Si se confirma una reserva pendiente
            if old_reserva.estado == 'pendiente' and self.estado == 'confirmada':
                if not self.tipo_habitacion.reservar_stock(self.cantidad_habitaciones):
                    raise ValidationError(f"No hay suficiente stock disponible para {self.tipo_habitacion.nombre}")
            
            # Si se cancela una reserva confirmada/activa
            elif old_reserva.estado in ['confirmada', 'activa'] and self.estado == 'cancelada':
                self.tipo_habitacion.liberar_stock(self.cantidad_habitaciones)
            
            # Si se completa una reserva activa
            elif old_reserva.estado == 'activa' and self.estado == 'completada':
                self.tipo_habitacion.liberar_stock(self.cantidad_habitaciones)

        super().save(*args, **kwargs)

    def confirmar(self):
        """Confirma la reserva y reserva el stock"""
        if self.estado == 'pendiente':
            if self.tipo_habitacion.reservar_stock(self.cantidad_habitaciones):
                self.estado = 'confirmada'
                self.save()
                return True
        return False

    def cancelar(self):
        """Cancela la reserva y libera el stock"""
        if self.estado in ['pendiente', 'confirmada']:
            if self.estado == 'confirmada':
                self.tipo_habitacion.liberar_stock(self.cantidad_habitaciones)
            self.estado = 'cancelada'
            self.save()
            return True
        return False

    def activar(self, habitacion_asignada=None):
        """Activa la reserva (check-in)"""
        if self.estado == 'confirmada':
            self.estado = 'activa'
            if habitacion_asignada:
                self.habitacion_asignada = habitacion_asignada
            self.save()
            return True
        return False

    def completar(self):
        """Completa la reserva (check-out) y libera el stock"""
        if self.estado == 'activa':
            self.estado = 'completada'
            self.tipo_habitacion.liberar_stock(self.cantidad_habitaciones)
            self.save()
            return True
        return False

    @property
    def precio_total(self):
        """Calcula el precio total de la reserva"""
        precio_base = self.tipo_habitacion.precio * self.cantidad_habitaciones
        
        # Aplicar descuento de promoción si existe
        if self.promocion:
            precio_base = precio_base * (1 - self.promocion.descuento / 100)
        
        # Agregar precio del plan si existe
        if self.plan:
            precio_base += self.plan.precio
        
        return precio_base

    def clean(self):
        if self.plan and self.promocion:
            raise ValidationError("La reserva no puede tener un plan y una promoción al mismo tiempo.")

    def calcular_total(self, incluir_servicios=True):
        """Calcula el monto total de la reserva en base a tipo de habitación, servicios, plan y promoción."""
        # Calcular precio base según tipo de habitación y cantidad de habitaciones
        precio_base = Decimal('0')
        if self.tipo_habitacion:
            precio_base = self.tipo_habitacion.precio * self.cantidad_habitaciones
        
        precio_servicios = Decimal('0')

        # Solo sumar servicios si la reserva ya existe en DB
        if incluir_servicios:
            precio_servicios = sum(Decimal(servicio.precio) for servicio in self.servicios.all())

        total = precio_base + precio_servicios

        if self.plan:
            total += self.plan.precio

        if self.promocion:
            descuento = (total * self.promocion.descuento) / 100
            total -= descuento

        return total

    def save(self, *args, **kwargs):
        # Primer save sin servicios, luego recalcular con servicios
        if self.pk:
            self.monto = self.calcular_total(incluir_servicios=True)
        else:
            self.monto = self.calcular_total(incluir_servicios=False)

        super().save(*args, **kwargs)

class Huesped(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    edad = models.PositiveIntegerField()
    genero = models.CharField(max_length=10, choices=[('M','Masculino'), ('F','Femenino'), ('O','Otro')])
    dni = models.CharField(max_length=20)
    reserva = models.ForeignKey('Reserva', on_delete=models.CASCADE, related_name='huespedes')

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class HuespedActivo(models.Model):
    """
    Representa a un huésped que está actualmente en el hotel.
    Se crea cuando una reserva se confirma (una entrada por cada Huesped
    ligado a esa reserva).
    """
    huesped = models.OneToOneField('Huesped', on_delete=models.CASCADE, related_name='activo')
    reserva = models.ForeignKey('Reserva', on_delete=models.CASCADE, related_name='huespedes_activos')
    habitacion = models.ForeignKey('habitaciones.Habitacion', on_delete=models.SET_NULL, null=True, blank=True)
    fecha_checkin = models.DateField(null=True, blank=True)
    fecha_checkout = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    def finalizar(self, fecha=None):
        """Marcar checkout (se puede llamar desde la vista cuando hace checkout)."""
        self.activo = False
        self.fecha_checkout = fecha or timezone.now().date()
        self.save()

    def __str__(self):
        return f"{self.huesped} — Hab: {self.habitacion or '-'}"
