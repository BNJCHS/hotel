from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

class UserProfile(models.Model):
    ROLES = [
        ('admin', 'Administrador'),
        ('recepcionista', 'Recepcionista'),
        ('limpieza', 'Personal de Limpieza'),
        ('mantenimiento', 'Mantenimiento'),
        ('gerente', 'Gerente'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLES, default='recepcionista')
    telefono = models.CharField(max_length=15, blank=True)
    cedula = models.CharField(max_length=20, unique=True)
    fecha_ingreso = models.DateField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()}"

class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=15)
    cedula = models.CharField(max_length=20, unique=True)
    direccion = models.TextField(blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.nombre} {self.apellido}"
    
    class Meta:
        ordering = ['-fecha_registro']

class Huesped(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='huespedes')
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    cedula = models.CharField(max_length=20)
    fecha_nacimiento = models.DateField()
    telefono = models.CharField(max_length=15, blank=True)
    
    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class PlanHospedaje(models.Model):
    TIPOS = [
        ('estandar', 'Estándar'),
        ('premium', 'Premium'),
        ('suite', 'Suite'),
        ('familiar', 'Familiar'),
    ]
    
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    descripcion = models.TextField()
    precio_base = models.DecimalField(max_digits=10, decimal_places=2)
    capacidad_personas = models.IntegerField(validators=[MinValueValidator(1)])
    incluye_desayuno = models.BooleanField(default=False)
    incluye_wifi = models.BooleanField(default=True)
    incluye_parking = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.nombre} - ${self.precio_base}"
    
    class Meta:
        ordering = ['precio_base']

class Servicio(models.Model):
    CATEGORIAS = [
        ('spa', 'Spa y Bienestar'),
        ('restaurante', 'Restaurante'),
        ('transporte', 'Transporte'),
        ('entretenimiento', 'Entretenimiento'),
        ('lavanderia', 'Lavandería'),
        ('otros', 'Otros'),
    ]
    
    nombre = models.CharField(max_length=100)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    disponible = models.BooleanField(default=True)
    horario_inicio = models.TimeField(null=True, blank=True)
    horario_fin = models.TimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.nombre} - ${self.precio}"

class Promocion(models.Model):
    TIPOS = [
        ('descuento', 'Descuento Porcentual'),
        ('fijo', 'Descuento Fijo'),
        ('2x1', '2x1'),
        ('upgrade', 'Upgrade Gratuito'),
    ]
    
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPOS)
    valor = models.DecimalField(max_digits=5, decimal_places=2, help_text="Porcentaje o valor fijo")
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    planes_aplicables = models.ManyToManyField(PlanHospedaje, blank=True)
    codigo_promocional = models.CharField(max_length=20, unique=True, blank=True)
    activa = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"
    
    def is_valid(self):
        from django.utils import timezone
        today = timezone.now().date()
        return self.activa and self.fecha_inicio <= today <= self.fecha_fin

class Empleado(models.Model):
    DEPARTAMENTOS = [
        ('recepcion', 'Recepción'),
        ('limpieza', 'Limpieza'),
        ('mantenimiento', 'Mantenimiento'),
        ('cocina', 'Cocina'),
        ('seguridad', 'Seguridad'),
        ('administracion', 'Administración'),
    ]
    
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    cedula = models.CharField(max_length=20, unique=True)
    telefono = models.CharField(max_length=15)
    email = models.EmailField()
    departamento = models.CharField(max_length=20, choices=DEPARTAMENTOS)
    salario = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_ingreso = models.DateField()
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.get_departamento_display()}"
    
    class Meta:
        ordering = ['departamento', 'apellido']
