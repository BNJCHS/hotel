#!/usr/bin/env python
"""
Script para crear perfiles para usuarios existentes que no tienen uno.
Ejecutar con: python create_missing_profiles.py
"""
import os
import django

# Configurar entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel_project.settings')
django.setup()

from django.contrib.auth.models import User
from usuarios.models import Profile

def create_missing_profiles():
    """Crea perfiles para usuarios que no tienen uno"""
    users_without_profile = []
    
    for user in User.objects.all():
        try:
            # Intenta acceder al perfil
            profile = user.profile
            print(f"Usuario {user.username} ya tiene perfil.")
        except User.profile.RelatedObjectDoesNotExist:
            # Si no existe, crea un nuevo perfil
            Profile.objects.create(user=user)
            users_without_profile.append(user.username)
            print(f"Perfil creado para el usuario {user.username}")
    
    if users_without_profile:
        print(f"\nSe crearon perfiles para {len(users_without_profile)} usuarios:")
        for username in users_without_profile:
            print(f"- {username}")
    else:
        print("\nTodos los usuarios ya tienen perfiles.")

if __name__ == "__main__":
    create_missing_profiles()