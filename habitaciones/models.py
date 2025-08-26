# app habitaciones/models.py

from django.db import models

class Habitacion(models.Model):
    TIPO_CHOICES = [
        ('simple', 'Simple'),
        ('doble', 'Doble'),
        ('suite', 'Suite'),
        ('presidencial','presidencial'),
    ]

    numero = models.IntegerField(unique=True)
    tipo = models.CharField(max_length=100, choices=TIPO_CHOICES)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    disponible = models.BooleanField(default=True)
    descripcion = models.TextField(blank=True, null=True)
    imagen = models.ImageField(upload_to='habitaciones/', blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)  # <--- NUEVO

    def __str__(self):
        return f'Habitación {self.numero} ({self.tipo})'
