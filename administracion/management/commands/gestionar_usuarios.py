from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from administracion.models import Rol, UsuarioRol


class Command(BaseCommand):
    help = 'Gestiona usuarios y sus permisos en el sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--listar',
            action='store_true',
            help='Listar todos los usuarios del sistema',
        )
        parser.add_argument(
            '--usuario',
            type=str,
            help='Mostrar información detallada de un usuario específico',
        )
        parser.add_argument(
            '--remover-rol',
            nargs=2,
            metavar=('USERNAME', 'ROL'),
            help='Remover un rol de un usuario (username rol)',
        )
        parser.add_argument(
            '--activar-usuario',
            type=str,
            help='Activar un usuario desactivado',
        )
        parser.add_argument(
            '--desactivar-usuario',
            type=str,
            help='Desactivar un usuario',
        )

    def handle(self, *args, **options):
        if options['listar']:
            self.listar_usuarios()
        elif options['usuario']:
            self.mostrar_usuario(options['usuario'])
        elif options['remover_rol']:
            username, rol_nombre = options['remover_rol']
            self.remover_rol(username, rol_nombre)
        elif options['activar_usuario']:
            self.activar_usuario(options['activar_usuario'])
        elif options['desactivar_usuario']:
            self.desactivar_usuario(options['desactivar_usuario'])
        else:
            self.print_help('manage.py', 'gestionar_usuarios')

    def listar_usuarios(self):
        """Lista todos los usuarios del sistema"""
        usuarios = User.objects.all().order_by('username')
        
        self.stdout.write(self.style.SUCCESS('\n=== USUARIOS DEL SISTEMA ==='))
        self.stdout.write(f'{"Usuario":<15} {"Email":<25} {"Staff":<6} {"Super":<6} {"Activo":<7} {"Roles"}')
        self.stdout.write('-' * 80)
        
        for user in usuarios:
            roles = UsuarioRol.objects.filter(usuario=user, activo=True)
            roles_str = ', '.join([rol.rol.get_nombre_display() for rol in roles]) or 'Sin roles'
            
            self.stdout.write(
                f'{user.username:<15} '
                f'{user.email:<25} '
                f'{"Sí" if user.is_staff else "No":<6} '
                f'{"Sí" if user.is_superuser else "No":<6} '
                f'{"Sí" if user.is_active else "No":<7} '
                f'{roles_str}'
            )

    def mostrar_usuario(self, username):
        """Muestra información detallada de un usuario"""
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'El usuario "{username}" no existe'))
            return

        from administracion.permissions import obtener_permisos_usuario
        
        self.stdout.write(self.style.SUCCESS(f'\n=== INFORMACIÓN DE {user.username} ==='))
        self.stdout.write(f'ID: {user.id}')
        self.stdout.write(f'Email: {user.email}')
        self.stdout.write(f'Nombre completo: {user.get_full_name() or "No especificado"}')
        self.stdout.write(f'Staff: {"Sí" if user.is_staff else "No"}')
        self.stdout.write(f'Superuser: {"Sí" if user.is_superuser else "No"}')
        self.stdout.write(f'Activo: {"Sí" if user.is_active else "No"}')
        self.stdout.write(f'Último login: {user.last_login or "Nunca"}')
        self.stdout.write(f'Fecha de registro: {user.date_joined}')
        
        # Mostrar roles
        roles = UsuarioRol.objects.filter(usuario=user, activo=True)
        self.stdout.write('\nRoles asignados:')
        if roles:
            for rol in roles:
                self.stdout.write(f'• {rol.rol.get_nombre_display()} (asignado: {rol.fecha_asignacion})')
        else:
            self.stdout.write('• Sin roles asignados')
        
        # Mostrar permisos
        permisos = obtener_permisos_usuario(user)
        if permisos:
            self.stdout.write('\nPermisos por módulo:')
            for modulo, acciones in permisos.items():
                self.stdout.write(f'• {modulo}: {", ".join(acciones)}')
        else:
            self.stdout.write('\nSin permisos asignados')

    def remover_rol(self, username, rol_nombre):
        """Remueve un rol de un usuario"""
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'El usuario "{username}" no existe'))
            return

        try:
            rol = Rol.objects.get(nombre=rol_nombre)
        except Rol.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'El rol "{rol_nombre}" no existe'))
            return

        try:
            usuario_rol = UsuarioRol.objects.get(usuario=user, rol=rol, activo=True)
            usuario_rol.activo = False
            usuario_rol.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Rol "{rol.get_nombre_display()}" removido de {username}'
                )
            )
        except UsuarioRol.DoesNotExist:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️ El usuario {username} no tiene el rol "{rol.get_nombre_display()}" asignado'
                )
            )

    def activar_usuario(self, username):
        """Activa un usuario"""
        try:
            user = User.objects.get(username=username)
            user.is_active = True
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Usuario {username} activado')
            )
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'El usuario "{username}" no existe'))

    def desactivar_usuario(self, username):
        """Desactiva un usuario"""
        try:
            user = User.objects.get(username=username)
            user.is_active = False
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Usuario {username} desactivado')
            )
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'El usuario "{username}" no existe'))