from django.db import models
from django.contrib.auth.models import User
from habitaciones.models import Habitacion
from administracion.models import Servicio  
import uuid

class Reserva(models.Model):
    METODOS_PAGO = [
        ('efectivo', 'Efectivo'),
        ('debito', 'Débito'),
        ('credito', 'Crédito'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    habitacion = models.ForeignKey(Habitacion, on_delete=models.CASCADE)
    servicios = models.ManyToManyField(Servicio, blank=True)
    fecha_reserva = models.DateTimeField(auto_now_add=True)
    confirmada = models.BooleanField(default=False)
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO, blank=True, null=True)
    token = models.CharField(max_length=64, default=uuid.uuid4, editable=False, unique=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    check_in = models.DateField(null=True, blank=True)
    check_out = models.DateField(null=True, blank=True)
    cantidad_huespedes = models.PositiveIntegerField(default=1)


    def __str__(self):
        return f"Reserva de {self.usuario.username} - Habitación {self.habitacion.numero}"
    

class Huesped(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    edad = models.PositiveIntegerField()
    genero = models.CharField(max_length=10, choices=[('M','Masculino'), ('F','Femenino'), ('O','Otro')])
    dni = models.CharField(max_length=20)
    reserva = models.ForeignKey('Reserva', on_delete=models.CASCADE, related_name='huespedes')

    def __str__(self):
        return f"{self.nombre} {self.apellido}"
