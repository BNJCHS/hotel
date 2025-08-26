from django.db import models
from django.contrib.auth.models import User
from habitaciones.models import Habitacion
from administracion.models import Servicio  # <- Importa el modelo desde la app correcta

class Reserva(models.Model):
    SERVICIOS = [
        ('medio', 'Medio'),
        ('completo', 'Completo'),
        ('personalizado', 'Personalizado'),
    ]

    METODOS_PAGO = [
        ('efectivo', 'Efectivo'),
        ('debito', 'Débito'),
        ('credito', 'Crédito'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    habitacion = models.ForeignKey(Habitacion, on_delete=models.CASCADE)
    servicios = models.ManyToManyField(Servicio, blank=True)
    fecha_reserva = models.DateTimeField(auto_now_add=True)
    servicio = models.CharField(max_length=20, choices=SERVICIOS)
    confirmada = models.BooleanField(default=False)
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO, blank=True, null=True)

    def __str__(self):
        return f"Reserva de {self.usuario.username} - Habitación {self.habitacion.numero}"