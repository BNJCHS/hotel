from django.contrib import admin
from .models import TipoHabitacion, Habitacion

@admin.register(TipoHabitacion)
class TipoHabitacionAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'precio', 'capacidad', 'stock_total', 'stock_disponible', 'porcentaje_ocupacion', 'activo']
    list_filter = ['activo', 'capacidad']
    search_fields = ['nombre', 'descripcion']
    readonly_fields = ['porcentaje_ocupacion']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'descripcion', 'imagen')
        }),
        ('Capacidad y Precio', {
            'fields': ('capacidad', 'precio')
        }),
        ('Gestión de Stock', {
            'fields': ('stock_total', 'stock_disponible')
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
    )
    
    def porcentaje_ocupacion(self, obj):
        return f"{obj.porcentaje_ocupacion()}%"
    porcentaje_ocupacion.short_description = 'Ocupación'

@admin.register(Habitacion)
class HabitacionAdmin(admin.ModelAdmin):
    list_display = ['numero', 'tipo_habitacion', 'precio', 'capacidad', 'disponible', 'en_mantenimiento']
    list_filter = ['tipo_habitacion', 'disponible', 'en_mantenimiento']
    search_fields = ['numero', 'observaciones']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('numero', 'tipo_habitacion')
        }),
        ('Estado', {
            'fields': ('disponible', 'en_mantenimiento', 'observaciones')
        }),
    )
    
    def precio(self, obj):
        return obj.precio
    precio.short_description = 'Precio'
    
    def capacidad(self, obj):
        return obj.capacidad
    capacidad.short_description = 'Capacidad'
