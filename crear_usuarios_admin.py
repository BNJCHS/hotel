#!/usr/bin/env python
"""
Script para crear usuarios de administración con diferentes roles
"""
import os
import django
import sys
from datetime import datetime

# Configurar entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel_project.settings')
django.setup()

# Importar modelos necesarios
from django.contrib.auth.models import User
from administracion.models import Rol, UsuarioRol
from django.db import transaction

# Definir los usuarios a crear con sus roles
USUARIOS = [
    {
        'username': 'super_admin',
        'email': 'super_admin@hotel.com',
        'password': 'Admin123!',
        'first_name': 'Super',
        'last_name': 'Administrador',
        'rol': 'super_admin',
        'is_staff': True,
    },
    {
        'username': 'admin_general',
        'email': 'admin@hotel.com',
        'password': 'Admin123!',
        'first_name': 'Admin',
        'last_name': 'General',
        'rol': 'admin_general',
        'is_staff': True,
    },
    {
        'username': 'recepcionista',
        'email': 'recepcion@hotel.com',
        'password': 'Recep123!',
        'first_name': 'Recepción',
        'last_name': 'Hotel',
        'rol': 'recepcionista',
        'is_staff': True,
    },
    {
        'username': 'solo_lectura',
        'email': 'lectura@hotel.com',
        'password': 'Lectura123!',
        'first_name': 'Usuario',
        'last_name': 'Lectura',
        'rol': 'solo_lectura',
        'is_staff': True,
    },
]

def crear_usuario(datos_usuario):
    """Crea un usuario y le asigna un rol"""
    username = datos_usuario['username']
    email = datos_usuario['email']
    password = datos_usuario['password']
    first_name = datos_usuario['first_name']
    last_name = datos_usuario['last_name']
    rol_nombre = datos_usuario['rol']
    is_staff = datos_usuario['is_staff']
    
    # Verificar si el usuario ya existe
    if User.objects.filter(username=username).exists():
        user = User.objects.get(username=username)
        print(f"El usuario {username} ya existe. Actualizando datos...")
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.is_staff = is_staff
        user.set_password(password)
        user.save()
    else:
        # Crear nuevo usuario
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_staff=is_staff
        )
        print(f"Usuario {username} creado correctamente.")
    
    # Asignar rol
    try:
        rol = Rol.objects.get(nombre=rol_nombre)
        # Verificar si ya tiene el rol asignado
        if UsuarioRol.objects.filter(usuario=user, rol=rol).exists():
            usuario_rol = UsuarioRol.objects.get(usuario=user, rol=rol)
            if not usuario_rol.activo:
                usuario_rol.activo = True
                usuario_rol.save()
                print(f"Rol {rol} reactivado para {username}.")
            else:
                print(f"El usuario {username} ya tiene el rol {rol}.")
        else:
            UsuarioRol.objects.create(usuario=user, rol=rol)
            print(f"Rol {rol} asignado a {username}.")
    except Rol.DoesNotExist:
        print(f"Error: El rol {rol_nombre} no existe en el sistema.")
        return None
    
    return {
        'username': username,
        'email': email,
        'password': password,
        'rol': rol.get_nombre_display(),
        'url_acceso': 'http://localhost:8000/administracion/login/'
    }

def generar_archivo_credenciales(usuarios_creados):
    """Genera un archivo txt con las credenciales de los usuarios creados"""
    fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nombre_archivo = f"credenciales_admin_{fecha}.txt"
    ruta_archivo = os.path.join(os.path.dirname(os.path.abspath(__file__)), nombre_archivo)
    
    with open(ruta_archivo, 'w') as f:
        f.write("=== CREDENCIALES DE ACCESO AL SISTEMA DE ADMINISTRACIÓN ===\n\n")
        f.write(f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
        f.write("URL de acceso: http://localhost:8000/administracion/login/\n\n")
        
        for usuario in usuarios_creados:
            if usuario:  # Solo incluir usuarios creados correctamente
                f.write(f"=== USUARIO: {usuario['username']} ===\n")
                f.write(f"Rol: {usuario['rol']}\n")
                f.write(f"Email: {usuario['email']}\n")
                f.write(f"Contraseña: {usuario['password']}\n")
                f.write("\n")
    
    print(f"\nArchivo de credenciales generado: {nombre_archivo}")
    return nombre_archivo

def main():
    """Función principal"""
    print("=== CREACIÓN DE USUARIOS DE ADMINISTRACIÓN ===\n")
    
    # Verificar que existan los roles
    roles_requeridos = set(usuario['rol'] for usuario in USUARIOS)
    roles_existentes = set(Rol.objects.values_list('nombre', flat=True))
    
    roles_faltantes = roles_requeridos - roles_existentes
    if roles_faltantes:
        print(f"Error: Faltan los siguientes roles en el sistema: {', '.join(roles_faltantes)}")
        print("Ejecute primero el comando 'python manage.py init_roles' para crear los roles necesarios.")
        return
    
    # Crear usuarios con sus roles
    usuarios_creados = []
    with transaction.atomic():
        for datos_usuario in USUARIOS:
            usuario = crear_usuario(datos_usuario)
            usuarios_creados.append(usuario)
    
    # Generar archivo de credenciales
    archivo_credenciales = generar_archivo_credenciales(usuarios_creados)
    
    print("\n=== RESUMEN ===")
    print(f"Total de usuarios creados/actualizados: {len([u for u in usuarios_creados if u])}")
    print(f"Credenciales guardadas en: {archivo_credenciales}")
    print("\nPuede acceder al sistema con estas credenciales en: http://localhost:8000/administracion/login/")

if __name__ == "__main__":
    main()