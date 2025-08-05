from django.db import models
from django.contrib.auth.models import User
from habitaciones.models import Habitacion

class Reserva(models.Model):
    SERVICIOS = [
        ('medio', 'Medio'),
        ('completo', 'Completo'),
        ('personalizado', 'Personalizado'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    habitacion = models.ForeignKey(Habitacion, on_delete=models.CASCADE)
    fecha_reserva = models.DateTimeField(auto_now_add=True)
    servicio = models.CharField(max_length=20, choices=SERVICIOS)

    def __str__(self):
        return f"Reserva de {self.usuario.username} - Habitación {self.habitacion.numero}"
