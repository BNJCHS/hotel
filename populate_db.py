#!/usr/bin/env python
"""
Script para poblar la base de datos con datos de prueba.
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel_project.settings')
django.setup()

from habitaciones.models import TipoHabitacion, Habitacion
from django.contrib.auth.models import User

def populate_database():
    """Pobla la base de datos con datos de prueba."""
    
    print("Creando datos de prueba...")
    
    # Crear tipos de habitaciones
    tipos = [
        {
            'nombre': 'Habitación Simple',
            'precio': 80.00,
            'capacidad': 1,
            'descripcion': 'Habitación cómoda para una persona con todas las comodidades básicas.',
            'stock_total': 10,
            'stock_disponible': 8,
            'activo': True
        },
        {
            'nombre': 'Habitación Doble',
            'precio': 120.00,
            'capacidad': 2,
            'descripcion': 'Habitación espaciosa para dos personas con cama matrimonial.',
            'stock_total': 15,
            'stock_disponible': 12,
            'activo': True
        },
        {
            'nombre': 'Suite Familiar',
            'precio': 200.00,
            'capacidad': 4,
            'descripcion': 'Suite amplia ideal para familias con sala de estar separada.',
            'stock_total': 5,
            'stock_disponible': 4,
            'activo': True
        },
        {
            'nombre': 'Suite Presidencial',
            'precio': 350.00,
            'capacidad': 2,
            'descripcion': 'La mejor suite del hotel con vista panorámica y servicios premium.',
            'stock_total': 2,
            'stock_disponible': 2,
            'activo': True
        }
    ]
    
    for tipo_data in tipos:
        tipo, created = TipoHabitacion.objects.get_or_create(
            nombre=tipo_data['nombre'],
            defaults=tipo_data
        )
        if created:
            print(f"Creado tipo: {tipo.nombre}")
        else:
            print(f"Tipo ya existe: {tipo.nombre}")
    
    # Crear habitaciones individuales para cada tipo
    for tipo in TipoHabitacion.objects.all():
        for i in range(tipo.stock_total):
            numero = f"{tipo.nombre[:3].upper()}{i+1:03d}"
            habitacion, created = Habitacion.objects.get_or_create(
                numero=numero,
                defaults={
                    'tipo_habitacion': tipo,
                    'disponible': i < tipo.stock_disponible,
                    'en_mantenimiento': False,
                    'observaciones': f'Habitación {numero} - {tipo.nombre}'
                }
            )
            if created:
                print(f"Creada habitación: {numero}")
    
    # Establecer contraseña para el superusuario
    try:
        admin = User.objects.get(username='admin')
        admin.set_password('admin123')
        admin.save()
        print("Contraseña del admin establecida: admin123")
    except User.DoesNotExist:
        print("Usuario admin no encontrado")
    
    print("Base de datos poblada exitosamente!")

if __name__ == '__main__':
    populate_database()