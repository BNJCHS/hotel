from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from administracion.models import Rol, UsuarioRol


class Command(BaseCommand):
    help = 'Asigna un rol a un usuario específico'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Nombre de usuario')
        parser.add_argument('rol', type=str, help='Nombre del rol a asignar')
        parser.add_argument(
            '--staff',
            action='store_true',
            help='Marcar al usuario como staff (necesario para acceder al admin)',
        )
        parser.add_argument(
            '--superuser',
            action='store_true',
            help='Marcar al usuario como superuser',
        )
        parser.add_argument(
            '--listar-roles',
            action='store_true',
            help='Mostrar todos los roles disponibles',
        )
        parser.add_argument(
            '--ver-permisos',
            action='store_true',
            help='Mostrar los permisos del usuario después de asignar el rol',
        )

    def handle(self, *args, **options):
        if options['listar_roles']:
            self.listar_roles()
            return

        username = options['username']
        rol_nombre = options['rol']

        try:
            # Verificar que el usuario existe
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'El usuario "{username}" no existe')

        try:
            # Verificar que el rol existe
            rol = Rol.objects.get(nombre=rol_nombre)
        except Rol.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'El rol "{rol_nombre}" no existe')
            )
            self.listar_roles()
            return

        # Marcar como staff si se solicita
        if options['staff']:
            user.is_staff = True
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Usuario {username} marcado como staff')
            )

        # Marcar como superuser si se solicita
        if options['superuser']:
            user.is_superuser = True
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Usuario {username} marcado como superuser')
            )

        # Asignar el rol
        usuario_rol, created = UsuarioRol.objects.get_or_create(
            usuario=user,
            rol=rol,
            defaults={'activo': True}
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Rol "{rol.get_nombre_display()}" asignado exitosamente a {username}'
                )
            )
        else:
            if not usuario_rol.activo:
                usuario_rol.activo = True
                usuario_rol.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Rol "{rol.get_nombre_display()}" reactivado para {username}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️ El usuario {username} ya tiene el rol "{rol.get_nombre_display()}" asignado'
                    )
                )

        # Mostrar permisos si se solicita
        if options['ver_permisos']:
            self.mostrar_permisos_usuario(user)

    def listar_roles(self):
        """Muestra todos los roles disponibles"""
        roles = Rol.objects.all()
        if not roles:
            self.stdout.write(self.style.WARNING('No hay roles disponibles'))
            return

        self.stdout.write(self.style.SUCCESS('\n=== ROLES DISPONIBLES ==='))
        for rol in roles:
            self.stdout.write(f'• {rol.nombre}: {rol.get_nombre_display()}')

    def mostrar_permisos_usuario(self, user):
        """Muestra los permisos del usuario"""
        from administracion.permissions import obtener_permisos_usuario
        
        self.stdout.write(self.style.SUCCESS(f'\n=== PERMISOS DE {user.username} ==='))
        self.stdout.write(f'Staff: {user.is_staff}')
        self.stdout.write(f'Superuser: {user.is_superuser}')
        
        # Mostrar roles
        roles = UsuarioRol.objects.filter(usuario=user, activo=True)
        self.stdout.write('\nRoles asignados:')
        for rol in roles:
            self.stdout.write(f'• {rol.rol.get_nombre_display()}')
        
        # Mostrar permisos
        permisos = obtener_permisos_usuario(user)
        self.stdout.write('\nPermisos por módulo:')
        for modulo, acciones in permisos.items():
            self.stdout.write(f'• {modulo}: {", ".join(acciones)}')