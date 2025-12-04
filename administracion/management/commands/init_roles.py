from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from administracion.models import Rol, Permiso, RolPermiso, UsuarioRol


class Command(BaseCommand):
    help = 'Inicializa roles y permisos básicos del sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Elimina todos los roles y permisos existentes antes de crear los nuevos',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('Eliminando roles y permisos existentes...')
            UsuarioRol.objects.all().delete()
            RolPermiso.objects.all().delete()
            Rol.objects.all().delete()
            Permiso.objects.all().delete()

        # Crear permisos básicos
        permisos_data = [
            # Empleados
            ('empleados', 'ver', 'Ver empleados'),
            ('empleados', 'crear', 'Crear empleados'),
            ('empleados', 'editar', 'Editar empleados'),
            ('empleados', 'eliminar', 'Eliminar empleados'),
            
            # Habitaciones
            ('habitaciones', 'ver', 'Ver habitaciones'),
            ('habitaciones', 'crear', 'Crear habitaciones'),
            ('habitaciones', 'editar', 'Editar habitaciones'),
            ('habitaciones', 'eliminar', 'Eliminar habitaciones'),
            
            # Reservas
            ('reservas', 'ver', 'Ver reservas'),
            ('reservas', 'crear', 'Crear reservas'),
            ('reservas', 'editar', 'Editar reservas'),
            ('reservas', 'eliminar', 'Eliminar reservas'),
            ('reservas', 'confirmar', 'Confirmar reservas'),
            ('reservas', 'cancelar', 'Cancelar reservas'),
            
            # Huéspedes
            ('huespedes', 'ver', 'Ver huéspedes'),
            ('huespedes', 'crear', 'Crear huéspedes'),
            ('huespedes', 'editar', 'Editar huéspedes'),
            ('huespedes', 'eliminar', 'Eliminar huéspedes'),
            
            # Servicios
            ('servicios', 'ver', 'Ver servicios'),
            ('servicios', 'crear', 'Crear servicios'),
            ('servicios', 'editar', 'Editar servicios'),
            ('servicios', 'eliminar', 'Eliminar servicios'),
            
            # Planes
            ('planes', 'ver', 'Ver planes'),
            ('planes', 'crear', 'Crear planes'),
            ('planes', 'editar', 'Editar planes'),
            ('planes', 'eliminar', 'Eliminar planes'),
            
            # Promociones
            ('promociones', 'ver', 'Ver promociones'),
            ('promociones', 'crear', 'Crear promociones'),
            ('promociones', 'editar', 'Editar promociones'),
            ('promociones', 'eliminar', 'Eliminar promociones'),
            
            # Reportes
            ('reportes', 'ver', 'Ver reportes'),
            ('reportes', 'generar', 'Generar reportes'),
            ('reportes', 'exportar', 'Exportar reportes'),
            
            # Dashboard
            ('dashboard', 'ver', 'Ver dashboard'),
            
            # Configuración
            ('configuracion', 'ver', 'Ver configuración'),
            ('configuracion', 'editar', 'Editar configuración'),
            
            # Usuarios y roles
            ('usuarios', 'ver', 'Ver usuarios'),
            ('usuarios', 'crear', 'Crear usuarios'),
            ('usuarios', 'editar', 'Editar usuarios'),
            ('usuarios', 'eliminar', 'Eliminar usuarios'),
            ('roles', 'ver', 'Ver roles'),
            ('roles', 'asignar', 'Asignar roles'),
            ('roles', 'crear', 'Crear roles'),
            ('roles', 'editar', 'Editar roles'),
        ]

        self.stdout.write('Creando permisos...')
        permisos_creados = {}
        for modulo, accion, descripcion in permisos_data:
            permiso, created = Permiso.objects.get_or_create(
                modulo=modulo,
                accion=accion,
                defaults={'descripcion': descripcion}
            )
            permisos_creados[f"{modulo}_{accion}"] = permiso
            if created:
                self.stdout.write(f'  ✓ Permiso creado: {descripcion}')

        # Crear roles básicos
        roles_data = [
            ('super_admin', 'Acceso completo al sistema'),
            ('admin_general', 'Administrador del hotel con acceso a la mayoría de funciones'),
            ('recepcionista', 'Manejo de reservas y huéspedes'),
            ('solo_lectura', 'Acceso básico de solo lectura'),
            ('marketing', 'Gestión de promociones, planes y servicios'),
        ]

        self.stdout.write('Creando roles...')
        roles_creados = {}
        for nombre, descripcion in roles_data:
            rol, created = Rol.objects.get_or_create(
                nombre=nombre,
                defaults={
                    'descripcion': descripcion
                }
            )
            roles_creados[nombre] = rol
            if created:
                self.stdout.write(f'  ✓ Rol creado: {rol.get_nombre_display()}')

        # Asignar permisos a roles
        self.stdout.write('Asignando permisos a roles...')
        
        # Super Admin - todos los permisos
        super_admin = roles_creados['super_admin']
        for permiso in permisos_creados.values():
            RolPermiso.objects.get_or_create(rol=super_admin, permiso=permiso)
        
        # Administrador General - casi todos los permisos excepto gestión de usuarios/roles
        admin_general = roles_creados['admin_general']
        permisos_admin = [p for key, p in permisos_creados.items() 
                         if not key.startswith('usuarios_') and not key.startswith('roles_')]
        permisos_admin.extend([permisos_creados['usuarios_ver'], permisos_creados['roles_ver']])
        for permiso in permisos_admin:
            RolPermiso.objects.get_or_create(rol=admin_general, permiso=permiso)
        
        # Recepcionista - reservas, huéspedes, habitaciones (ver)
        recepcionista = roles_creados['recepcionista']
        permisos_recepcionista = [
            'dashboard_ver',
            'reservas_ver', 'reservas_crear', 'reservas_editar', 'reservas_confirmar', 'reservas_cancelar',
            'huespedes_ver', 'huespedes_crear', 'huespedes_editar',
            'habitaciones_ver',
            'servicios_ver',
            'planes_ver',
            'promociones_ver',
        ]
        for permiso_key in permisos_recepcionista:
            if permiso_key in permisos_creados:
                RolPermiso.objects.get_or_create(rol=recepcionista, permiso=permisos_creados[permiso_key])
        
        # Solo Lectura - solo ver información básica
        solo_lectura = roles_creados['solo_lectura']
        permisos_solo_lectura = [
            'dashboard_ver',
            'habitaciones_ver',
            'servicios_ver',
            'planes_ver',
            'promociones_ver',
            'reservas_ver',
            'huespedes_ver',
        ]
        for permiso_key in permisos_solo_lectura:
            if permiso_key in permisos_creados:
                RolPermiso.objects.get_or_create(rol=solo_lectura, permiso=permisos_creados[permiso_key])

        # Marketing - gestionar sólo promociones, planes y servicios
        marketing = roles_creados['marketing']
        permisos_marketing = [
            'dashboard_ver',
            # Servicios
            'servicios_ver', 'servicios_crear', 'servicios_editar', 'servicios_eliminar',
            # Planes
            'planes_ver', 'planes_crear', 'planes_editar', 'planes_eliminar',
            # Promociones
            'promociones_ver', 'promociones_crear', 'promociones_editar', 'promociones_eliminar',
        ]
        for permiso_key in permisos_marketing:
            if permiso_key in permisos_creados:
                RolPermiso.objects.get_or_create(rol=marketing, permiso=permisos_creados[permiso_key])

        # Asignar rol de super admin al primer superusuario
        try:
            superuser = User.objects.filter(is_superuser=True).first()
            if superuser:
                UsuarioRol.objects.get_or_create(
                    usuario=superuser,
                    rol=super_admin,
                    defaults={'asignado_por': superuser}
                )
                self.stdout.write(f'  ✓ Rol Super Admin asignado a {superuser.username}')
        except Exception as e:
            self.stdout.write(f'  ⚠ No se pudo asignar rol al superusuario: {e}')

        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Sistema de roles inicializado correctamente!\n'
                f'  - {len(permisos_creados)} permisos creados\n'
                f'  - {len(roles_creados)} roles creados\n'
                f'  - Permisos asignados a roles'
            )
        )
