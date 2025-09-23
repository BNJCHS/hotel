# app habitaciones/models.py

from django.db import models

class TipoHabitacion(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    capacidad = models.PositiveIntegerField(default=1)
    stock_total = models.PositiveIntegerField(default=0, help_text="Cantidad total de habitaciones de este tipo")
    stock_disponible = models.PositiveIntegerField(default=0, help_text="Cantidad disponible para reservar")
    descripcion = models.TextField(blank=True, null=True)
    imagen = models.ImageField(upload_to='tipos_habitaciones/', blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Tipo de Habitación"
        verbose_name_plural = "Tipos de Habitaciones"

    def __str__(self):
        return f"{self.nombre} (capacidad {self.capacidad}) - Stock: {self.stock_disponible}/{self.stock_total}"

    def tiene_disponibilidad(self, cantidad=1):
        """Verifica si hay suficiente stock disponible"""
        return self.stock_disponible >= cantidad and self.activo

    def reservar_stock(self, cantidad=1):
        """Reduce el stock disponible al hacer una reserva"""
        if self.tiene_disponibilidad(cantidad):
            self.stock_disponible -= cantidad
            self.save()
            return True
        return False

    def liberar_stock(self, cantidad=1):
        """Aumenta el stock disponible al cancelar una reserva"""
        if self.stock_disponible + cantidad <= self.stock_total:
            self.stock_disponible += cantidad
            self.save()
            return True
        return False

    def porcentaje_ocupacion(self):
        """Calcula el porcentaje de ocupación"""
        if self.stock_total == 0:
            return 0
        ocupadas = self.stock_total - self.stock_disponible
        return round((ocupadas / self.stock_total) * 100, 2)


class Habitacion(models.Model):
    """
    Modelo para habitaciones físicas individuales.
    Ahora cada habitación pertenece a un tipo específico.
    """
    numero = models.CharField(max_length=10, unique=True, help_text="Número o identificador de la habitación")
    tipo_habitacion = models.ForeignKey(TipoHabitacion, on_delete=models.CASCADE, related_name='habitaciones')
    disponible = models.BooleanField(default=True, help_text="Si la habitación está disponible para uso")
    en_mantenimiento = models.BooleanField(default=False, help_text="Si la habitación está en mantenimiento")
    observaciones = models.TextField(blank=True, null=True, help_text="Observaciones específicas de esta habitación")

    class Meta:
        verbose_name = "Habitación"
        verbose_name_plural = "Habitaciones"
        ordering = ['numero']

    def __str__(self):
        return f'Habitación {self.numero} ({self.tipo_habitacion.nombre})'

    @property
    def precio(self):
        """El precio se obtiene del tipo de habitación"""
        return self.tipo_habitacion.precio

    @property
    def capacidad(self):
        """La capacidad se obtiene del tipo de habitación"""
        return self.tipo_habitacion.capacidad

    def esta_disponible(self):
        """Verifica si la habitación está disponible para reservar"""
        return self.disponible and not self.en_mantenimiento and self.tipo_habitacion.activo
