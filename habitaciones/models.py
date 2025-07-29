from django.db import models

class Habitacion(models.Model):
    TIPO_CHOICES = [
        ('simple', 'Simple'),
        ('doble', 'Doble'),
        ('suite', 'Suite'),
    ]

    numero = models.IntegerField(unique=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    disponible = models.BooleanField(default=True)
    descripcion = models.TextField(blank=True, null=True)
    imagen = models.ImageField(upload_to='habitaciones/', blank=True, null=True)

    def __str__(self):
        return f'Habitación {self.numero} ({self.tipo})'
