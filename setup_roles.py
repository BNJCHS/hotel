#!/usr/bin/env python
"""
Script para configurar el sistema de roles y permisos
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel_project.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.db import connection
from administracion.models import Rol, Permiso, RolPermiso

def check_table_exists(table_name):
    """Verificar si una tabla existe en la base de datos"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = %s
        """, [connection.settings_dict['NAME'], table_name])
        return cursor.fetchone()[0] > 0

def main():
    print("🔧 Configurando sistema de roles y permisos...")
    
    # Verificar si las tablas existen
    if not check_table_exists('administracion_rol'):
        print("❌ Las tablas del sistema de roles no existen.")
        print("📝 Aplicando migraciones...")
        try:
            execute_from_command_line(['manage.py', 'migrate'])
            print("✅ Migraciones aplicadas correctamente.")
        except Exception as e:
            print(f"❌ Error al aplicar migraciones: {e}")
            return False
    else:
        print("✅ Las tablas del sistema de roles ya existen.")
    
    # Verificar si ya existen roles
    if Rol.objects.exists():
        print("✅ El sistema de roles ya está inicializado.")
        print(f"📊 Roles existentes: {Rol.objects.count()}")
        print(f"📊 Permisos existentes: {Permiso.objects.count()}")
        return True
    
    print("🚀 Inicializando roles y permisos...")
    try:
        # Ejecutar el comando de inicialización
        execute_from_command_line(['manage.py', 'init_roles'])
        print("✅ Sistema de roles inicializado correctamente.")
        return True
    except Exception as e:
        print(f"❌ Error al inicializar roles: {e}")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)