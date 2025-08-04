from django.db import models
from django.contrib.auth.models import User
from habitaciones.models import Habitacion 

class ReservaTemp(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    habitacion = models.ForeignKey(Habitacion, on_delete=models.CASCADE)
    fecha_reserva = models.DateTimeField(auto_now_add=True)
    
    SERVICIOS = [
        ('medio', 'Medio'),
        ('completo', 'Completo'),
        ('personalizado', 'Personalizado'),
    ]
    servicio = models.CharField(max_length=20, choices=SERVICIOS, null=True, blank=True)

    def __str__(self):
        return f"{self.usuario.username} - {self.habitacion} ({self.servicio or 'sin servicio'})"
