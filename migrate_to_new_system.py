#!/usr/bin/env python
"""
Script para migrar del sistema anterior al nuevo sistema de tipos de habitaciones con stock.
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel_project.settings')
django.setup()

from habitaciones.models import Habitacion, TipoHabitacion
from reservas.models import Reserva
from django.db import transaction

def migrate_data():
    """Migra los datos del sistema anterior al nuevo sistema."""
    
    print("Iniciando migración de datos...")
    
    with transaction.atomic():
        # 1. Crear tipos de habitaciones basados en los tipos existentes
        tipos_existentes = Habitacion.objects.values_list('tipo', flat=True).distinct()
        
        tipos_mapping = {}
        
        for tipo_nombre in tipos_existentes:
            if not tipo_nombre:
                continue
                
            # Obtener una habitación de este tipo para extraer datos
            habitacion_ejemplo = Habitacion.objects.filter(tipo=tipo_nombre).first()
            
            if habitacion_ejemplo:
                # Crear o obtener el tipo de habitación
                tipo_habitacion, created = TipoHabitacion.objects.get_or_create(
                    nombre=tipo_nombre,
                    defaults={
                        'precio': habitacion_ejemplo.precio or 100.00,
                        'capacidad': habitacion_ejemplo.capacidad or 2,
                        'descripcion': habitacion_ejemplo.descripcion or f'Habitación tipo {tipo_nombre}',
                        'imagen': habitacion_ejemplo.imagen,
                        'stock_total': Habitacion.objects.filter(tipo=tipo_nombre).count(),
                        'stock_disponible': Habitacion.objects.filter(tipo=tipo_nombre, disponible=True).count(),
                        'activo': True
                    }
                )
                
                tipos_mapping[tipo_nombre] = tipo_habitacion
                
                if created:
                    print(f"Creado tipo de habitación: {tipo_nombre}")
                else:
                    print(f"Tipo de habitación ya existe: {tipo_nombre}")
        
        # 2. Actualizar habitaciones para usar tipo_habitacion
        for habitacion in Habitacion.objects.all():
            if habitacion.tipo and habitacion.tipo in tipos_mapping:
                # Crear una nueva habitación con el nuevo modelo
                # (esto se hará después de aplicar las migraciones)
                pass
        
        print("Migración completada exitosamente!")

if __name__ == '__main__':
    migrate_data()