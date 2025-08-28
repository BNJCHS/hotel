from django.db import models
from django.contrib.auth.models import User
from habitaciones.models import Habitacion
from administracion.models import Servicio  
import uuid

import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from habitaciones.models import Habitacion
from administracion.models import Servicio


class Reserva(models.Model):
    METODOS_PAGO = [
        ('efectivo', 'Efectivo'),
        ('debito', 'Débito'),
        ('credito', 'Crédito'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    habitacion = models.ForeignKey(Habitacion, on_delete=models.CASCADE)
    servicios = models.ManyToManyField(Servicio, blank=True)

    # Nuevos campos para relación con administración
    plan = models.ForeignKey(
        'administracion.Plan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    promocion = models.ForeignKey(
        'administracion.Promocion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    fecha_reserva = models.DateTimeField(auto_now_add=True)
    confirmada = models.BooleanField(default=False)
    metodo_pago = models.CharField(
        max_length=20,
        choices=METODOS_PAGO,
        blank=True,
        null=True
    )
    token = models.CharField(
        max_length=64,
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    monto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    check_in = models.DateField(null=True, blank=True)
    check_out = models.DateField(null=True, blank=True)
    cantidad_huespedes = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['-fecha_reserva']

    def __str__(self):
        detalle = f"Reserva de {self.usuario.username} - Habitación {self.habitacion.numero}"
        if self.plan:
            detalle += f" - Plan: {self.plan.nombre}"
        if self.promocion:
            detalle += f" - Promoción: {self.promocion.nombre}"
        return detalle

    def clean(self):
        # No permitir tener plan y promoción al mismo tiempo
        if self.plan and self.promocion:
            raise ValidationError("La reserva no puede tener un plan y una promoción al mismo tiempo.")

    def calcular_total(self):
        """Calcula el monto total de la reserva en base a habitación, servicios, plan y promoción."""
        precio_base = self.habitacion.precio if self.habitacion else 0
        precio_servicios = sum(servicio.precio for servicio in self.servicios.all())

        total = precio_base + precio_servicios

        if self.plan:
            total += self.plan.precio

        if self.promocion:
            descuento = (total * self.promocion.descuento) / 100
            total -= descuento

        return total

    def save(self, *args, **kwargs):
        # Siempre recalcular el monto antes de guardar
        self.monto = self.calcular_total()
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
