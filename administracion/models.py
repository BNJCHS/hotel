from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from habitaciones.models import Habitacion

class Empleado(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(max_length=20, unique=True)
    puesto = models.CharField(max_length=100)
    salario = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    class Meta:
        ordering = ["apellido", "nombre"]

    def __str__(self):
        return f"{self.apellido}, {self.nombre} - {self.puesto}"


class Plan(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    imagen = models.ImageField(upload_to='planes/', null=True, blank=True)
    habitacion = models.ForeignKey(Habitacion, on_delete=models.CASCADE)  # Habitación asociada al plan

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Promocion(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField()
    descuento = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Porcentaje (0-100)"
    )
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    imagen = models.ImageField(upload_to='promociones/', null=True, blank=True)

    class Meta:
        ordering = ["-fecha_inicio", "nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.descuento}%)"
class Servicio(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

class Huesped(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(max_length=20, unique=True)
    telefono = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)

    class Meta:
        ordering = ["apellido", "nombre"]

    def __str__(self):
        return f"{self.apellido}, {self.nombre}"


class Rol(models.Model):
    """Modelo para definir roles del sistema"""
    ROLES_CHOICES = [
        ('super_admin', 'Super Administrador'),
        ('admin_general', 'Administrador General'),
        ('admin_habitaciones', 'Administrador de Habitaciones'),
        ('admin_empleados', 'Administrador de Empleados'),
        ('admin_servicios', 'Administrador de Servicios'),
        ('admin_huespedes', 'Administrador de Huéspedes'),
        ('admin_reservas', 'Administrador de Reservas'),
        ('recepcionista', 'Recepcionista'),
        ('solo_lectura', 'Solo Lectura'),
    ]
    
    nombre = models.CharField(max_length=50, choices=ROLES_CHOICES, unique=True)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['nombre']
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
    
    def __str__(self):
        return self.get_nombre_display()


class Permiso(models.Model):
    """Modelo para definir permisos específicos"""
    MODULOS_CHOICES = [
        ('empleados', 'Empleados'),
        ('habitaciones', 'Habitaciones'),
        ('planes', 'Planes'),
        ('promociones', 'Promociones'),
        ('servicios', 'Servicios'),
        ('huespedes', 'Huéspedes'),
        ('reservas', 'Reservas'),
        ('usuarios', 'Usuarios'),
        ('dashboard', 'Dashboard'),
    ]
    
    ACCIONES_CHOICES = [
        ('ver', 'Ver'),
        ('crear', 'Crear'),
        ('editar', 'Editar'),
        ('eliminar', 'Eliminar'),
        ('exportar', 'Exportar'),
        ('aprobar', 'Aprobar'),
    ]
    
    modulo = models.CharField(max_length=50, choices=MODULOS_CHOICES)
    accion = models.CharField(max_length=50, choices=ACCIONES_CHOICES)
    descripcion = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['modulo', 'accion']
        ordering = ['modulo', 'accion']
        verbose_name = 'Permiso'
        verbose_name_plural = 'Permisos'
    
    def __str__(self):
        return f"{self.get_modulo_display()} - {self.get_accion_display()}"


class RolPermiso(models.Model):
    """Modelo intermedio para asignar permisos a roles"""
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE, related_name='permisos')
    permiso = models.ForeignKey(Permiso, on_delete=models.CASCADE, related_name='roles')
    
    class Meta:
        unique_together = ['rol', 'permiso']
        verbose_name = 'Rol-Permiso'
        verbose_name_plural = 'Roles-Permisos'
    
    def __str__(self):
        return f"{self.rol} - {self.permiso}"


class UsuarioRol(models.Model):
    """Modelo para asignar roles a usuarios"""
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='roles_admin')
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE, related_name='usuarios')
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    asignado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='roles_asignados')
    
    class Meta:
        unique_together = ['usuario', 'rol']
        ordering = ['-fecha_asignacion']
        verbose_name = 'Usuario-Rol'
        verbose_name_plural = 'Usuarios-Roles'
    
    def __str__(self):
        return f"{self.usuario.username} - {self.rol}"
