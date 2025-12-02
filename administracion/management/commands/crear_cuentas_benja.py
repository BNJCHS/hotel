from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from administracion.models import Rol, UsuarioRol
from django.utils import timezone
import secrets
import os


class Command(BaseCommand):
    help = "Crea cuentas nuevas para benjaminchaves34@gmail.com y asigna roles: usuario, recepcionista, solo_lectura, marketing"

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, default='benjaminchaves34@gmail.com', help='Email a usar para todas las cuentas')
        parser.add_argument('--prefix', type=str, default='benja', help='Prefijo para los usernames (ej: benja_usuario)')
        parser.add_argument('--no-overwrite-password', action='store_true', help='No sobreescribir contraseña si el usuario ya existe')

    def handle(self, *args, **options):
        email = options['email']
        prefix = options['prefix']
        overwrite_pwd = not options['no_overwrite_password']

        accounts = [
            {'username': f'{prefix}_usuario', 'role': None, 'is_staff': False, 'full_name': ('Usuario', 'Hotel')},
            {'username': f'{prefix}_recepcionista', 'role': 'recepcionista', 'is_staff': True, 'full_name': ('Recepcionista', 'Hotel')},
            {'username': f'{prefix}_lectura', 'role': 'solo_lectura', 'is_staff': True, 'full_name': ('Lectura', 'Hotel')},
            {'username': f'{prefix}_marketing', 'role': 'marketing', 'is_staff': True, 'full_name': ('Marketing', 'Hotel')},
        ]

        # Verificar roles requeridos
        required_roles = {acc['role'] for acc in accounts if acc['role']}
        existing_roles = set(Rol.objects.values_list('nombre', flat=True))
        missing = required_roles - existing_roles
        if missing:
            self.stderr.write(self.style.ERROR(f'Faltan roles: {", ".join(sorted(missing))}. Ejecuta "python manage.py init_roles" primero.'))
            return

        created_info = []
        for acc in accounts:
            username = acc['username']
            first_name, last_name = acc['full_name']
            pwd = secrets.token_urlsafe(8)

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'is_staff': acc['is_staff'],
                }
            )

            if created:
                user.set_password(pwd)
                user.save()
                self.stdout.write(self.style.SUCCESS(f'✅ Usuario creado: {username} (staff={acc["is_staff"]})'))
            else:
                # Actualizar datos
                user.email = email
                user.first_name = first_name
                user.last_name = last_name
                user.is_staff = acc['is_staff']
                if overwrite_pwd:
                    user.set_password(pwd)
                user.save()
                self.stdout.write(self.style.WARNING(f'ℹ Usuario existente actualizado: {username}'))

            # Asignar rol si corresponde
            if acc['role']:
                rol = Rol.objects.get(nombre=acc['role'])
                ur, ur_created = UsuarioRol.objects.get_or_create(usuario=user, rol=rol, defaults={'activo': True})
                if ur_created:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Rol asignado: {rol.get_nombre_display()} → {username}'))
                else:
                    if not ur.activo:
                        ur.activo = True
                        ur.save()
                        self.stdout.write(self.style.SUCCESS(f'  ✓ Rol reactivado: {rol.get_nombre_display()} → {username}'))
                    else:
                        self.stdout.write(self.style.WARNING(f'  ⚠ {username} ya tiene rol {rol.get_nombre_display()}'))

            created_info.append({
                'username': username,
                'email': email,
                'password': pwd,
                'is_staff': acc['is_staff'],
                'role': acc['role'] or 'N/A',
            })

        # Guardar credenciales en archivo
        try:
            ts = timezone.now().strftime('%Y%m%d_%H%M%S')
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            fname = os.path.join(base_dir, f'credenciales_benja_{ts}.txt')
            with open(fname, 'w', encoding='utf-8') as f:
                f.write('=== CREDENCIALES DE CUENTAS BENJA ===\n')
                f.write('URL acceso admin: http://127.0.0.1:8000/administracion/login/\n')
                f.write('URL sitio hotel: http://127.0.0.1:8000/\n\n')
                for info in created_info:
                    f.write(f"Usuario: {info['username']}\n")
                    f.write(f"Email: {info['email']}\n")
                    f.write(f"Contraseña: {info['password']}\n")
                    f.write(f"Staff: {info['is_staff']}\n")
                    f.write(f"Rol: {info['role']}\n\n")
            self.stdout.write(self.style.SUCCESS(f'📝 Credenciales guardadas en: {fname}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'No se pudieron guardar credenciales: {e}'))
