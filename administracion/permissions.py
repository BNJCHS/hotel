from functools import wraps
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from .models import UsuarioRol, RolPermiso


def usuario_tiene_permiso(usuario, modulo, accion):
    """
    Verifica si un usuario tiene un permiso específico
    """
    if not usuario.is_authenticated:
        return False
    
    # Super usuarios siempre tienen acceso
    if usuario.is_superuser:
        return True

    # Acceso defensivo: cualquier usuario staff puede ver el dashboard
    if modulo == 'dashboard' and accion == 'ver' and usuario.is_staff:
        return True
    
    # Verificar si el usuario tiene roles activos
    roles_usuario = UsuarioRol.objects.filter(
        usuario=usuario, 
        activo=True,
        rol__activo=True
    ).select_related('rol')
    
    if not roles_usuario.exists():
        return False
    
    # Verificar si alguno de los roles tiene el permiso requerido
    for usuario_rol in roles_usuario:
        rol = usuario_rol.rol
        
        # Super admin tiene todos los permisos
        if rol.nombre == 'super_admin':
            return True
        
        # Verificar permisos específicos del rol
        tiene_permiso = RolPermiso.objects.filter(
            rol=rol,
            permiso__modulo=modulo,
            permiso__accion=accion
        ).exists()
        
        if tiene_permiso:
            return True
    
    return False


def obtener_roles_usuario(usuario):
    """
    Obtiene todos los roles activos de un usuario
    """
    if not usuario.is_authenticated:
        return []
    
    return UsuarioRol.objects.filter(
        usuario=usuario,
        activo=True,
        rol__activo=True
    ).select_related('rol')


def es_super_admin(usuario):
    """
    Verifica si el usuario es super administrador
    """
    if not usuario.is_authenticated:
        return False
    
    if usuario.is_superuser:
        return True
    
    return UsuarioRol.objects.filter(
        usuario=usuario,
        rol__nombre='super_admin',
        activo=True,
        rol__activo=True
    ).exists()


def requiere_permiso(modulo, accion, redirect_url=None):
    """
    Decorador para verificar permisos en vistas
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Vista como rol: si está activa y el usuario es Super Admin, validar contra el rol simulado
            preview_role_id = request.session.get('role_preview_id')
            allow = True
            if preview_role_id and es_super_admin(request.user):
                try:
                    from .models import Rol, RolPermiso
                    preview_role = Rol.objects.get(id=preview_role_id, activo=True)
                    if preview_role.nombre == 'super_admin':
                        allow = True
                    else:
                        allow = RolPermiso.objects.filter(
                            rol=preview_role,
                            permiso__modulo=modulo,
                            permiso__accion=accion
                        ).exists()
                except Exception:
                    # Si falla, desactivar vista previa y verificar permisos reales
                    request.session.pop('role_preview_id', None)
                    allow = usuario_tiene_permiso(request.user, modulo, accion)
            else:
                allow = usuario_tiene_permiso(request.user, modulo, accion)

            if not allow:
                messages.error(
                    request,
                    f'No tienes permisos para {accion} en el módulo {modulo}.'
                )
                if redirect_url:
                    return redirect(redirect_url)
                return redirect('administracion:dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def requiere_staff_y_permiso(modulo, accion):
    """
    Decorador que combina staff_member_required con verificación de permisos
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Verificar que esté autenticado
            if not request.user.is_authenticated:
                messages.error(request, 'Debes iniciar sesión para acceder al panel de administración.')
                return redirect('administracion:admin_login')
            
            # Verificar que sea staff, excepto si es Super Admin
            if not request.user.is_staff and not es_super_admin(request.user):
                messages.error(request, 'Acceso denegado. Se requieren permisos de staff.')
                return redirect('administracion:admin_login')
            
            # Verificar permisos específicos (soportando vista previa de rol)
            preview_role_id = request.session.get('role_preview_id')
            allow = True
            if preview_role_id and es_super_admin(request.user):
                try:
                    from .models import Rol, RolPermiso
                    preview_role = Rol.objects.get(id=preview_role_id, activo=True)
                    if preview_role.nombre == 'super_admin':
                        allow = True
                    else:
                        allow = RolPermiso.objects.filter(
                            rol=preview_role,
                            permiso__modulo=modulo,
                            permiso__accion=accion
                        ).exists()
                except Exception:
                    request.session.pop('role_preview_id', None)
                    allow = usuario_tiene_permiso(request.user, modulo, accion)
            else:
                allow = usuario_tiene_permiso(request.user, modulo, accion)

            if not allow:
                messages.error(
                    request, 
                    f'No tienes permisos para {accion} en el módulo {modulo}.'
                )
                return redirect('administracion:dashboard')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def obtener_permisos_usuario(usuario):
    """
    Obtiene todos los permisos de un usuario organizados por módulo
    """
    if not usuario.is_authenticated:
        return {}
    
    if usuario.is_superuser:
        # Super usuarios tienen todos los permisos
        from .models import Permiso
        permisos = Permiso.objects.all()
        permisos_dict = {}
        for permiso in permisos:
            if permiso.modulo not in permisos_dict:
                permisos_dict[permiso.modulo] = []
            permisos_dict[permiso.modulo].append(permiso.accion)
        return permisos_dict
    
    roles_usuario = obtener_roles_usuario(usuario)
    permisos_dict = {}
    
    for usuario_rol in roles_usuario:
        rol = usuario_rol.rol
        
        if rol.nombre == 'super_admin':
            # Super admin tiene todos los permisos
            from .models import Permiso
            permisos = Permiso.objects.all()
            for permiso in permisos:
                if permiso.modulo not in permisos_dict:
                    permisos_dict[permiso.modulo] = []
                if permiso.accion not in permisos_dict[permiso.modulo]:
                    permisos_dict[permiso.modulo].append(permiso.accion)
        else:
            # Obtener permisos específicos del rol
            rol_permisos = RolPermiso.objects.filter(rol=rol).select_related('permiso')
            for rol_permiso in rol_permisos:
                permiso = rol_permiso.permiso
                if permiso.modulo not in permisos_dict:
                    permisos_dict[permiso.modulo] = []
                if permiso.accion not in permisos_dict[permiso.modulo]:
                    permisos_dict[permiso.modulo].append(permiso.accion)
    
    # Asegurar acceso de staff al dashboard en el diccionario para templates
    if usuario.is_staff:
        acciones = permisos_dict.get('dashboard', [])
        if 'ver' not in acciones:
            acciones.append('ver')
            permisos_dict['dashboard'] = acciones

    return permisos_dict


class PermisosContextProcessor:
    """
    Context processor para agregar permisos del usuario a todos los templates
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_template_response(self, request, response):
        if hasattr(response, 'context_data') and response.context_data is not None:
            if request.user.is_authenticated:
                response.context_data['user_permissions'] = obtener_permisos_usuario(request.user)
                response.context_data['user_roles'] = [ur.rol for ur in obtener_roles_usuario(request.user)]
                response.context_data['is_super_admin'] = es_super_admin(request.user)
        return response


def convertir_permisos_para_template(permisos_dict):
    """
    Convierte el diccionario de permisos al formato esperado por el template
    """
    class PermisosModulo:
        def __init__(self, acciones):
            self.ver = 'ver' in acciones
            self.crear = 'crear' in acciones
            self.editar = 'editar' in acciones
            self.eliminar = 'eliminar' in acciones
            self.asignar = 'asignar' in acciones
            self.revocar = 'revocar' in acciones
    
    class PermisosTemplate:
        def __init__(self, permisos_dict):
            self.dashboard = PermisosModulo(permisos_dict.get('dashboard', []))
            self.usuarios = PermisosModulo(permisos_dict.get('usuarios', []))
            self.habitaciones = PermisosModulo(permisos_dict.get('habitaciones', []))
            self.empleados = PermisosModulo(permisos_dict.get('empleados', []))
            self.planes = PermisosModulo(permisos_dict.get('planes', []))
            self.promociones = PermisosModulo(permisos_dict.get('promociones', []))
            self.servicios = PermisosModulo(permisos_dict.get('servicios', []))
            self.huespedes = PermisosModulo(permisos_dict.get('huespedes', []))
            self.reservas = PermisosModulo(permisos_dict.get('reservas', []))
            self.roles = PermisosModulo(permisos_dict.get('roles', []))
    
    return PermisosTemplate(permisos_dict)


def permisos_context(request):
    """
    Context processor simple para templates
    """
    if request.user.is_authenticated:
        # Modo vista previa de rol (solo afecta templates/UI)
        preview_role_id = request.session.get('role_preview_id')
        preview_role = None
        permisos_raw = {}
        if preview_role_id:
            try:
                from .models import Rol, Permiso, RolPermiso
                preview_role = Rol.objects.get(id=preview_role_id, activo=True)
                if preview_role.nombre == 'super_admin':
                    # Super Admin: todos los permisos
                    permisos = Permiso.objects.all()
                    for permiso in permisos:
                        if permiso.modulo not in permisos_raw:
                            permisos_raw[permiso.modulo] = []
                        if permiso.accion not in permisos_raw[permiso.modulo]:
                            permisos_raw[permiso.modulo].append(permiso.accion)
                else:
                    # Permisos del rol específico
                    rol_permisos = RolPermiso.objects.filter(rol=preview_role).select_related('permiso')
                    for rp in rol_permisos:
                        permiso = rp.permiso
                        if permiso.modulo not in permisos_raw:
                            permisos_raw[permiso.modulo] = []
                        if permiso.accion not in permisos_raw[permiso.modulo]:
                            permisos_raw[permiso.modulo].append(permiso.accion)
            except Exception:
                # Si falla, desactivar preview y usar permisos reales
                request.session.pop('role_preview_id', None)
                permisos_raw = obtener_permisos_usuario(request.user)
        else:
            permisos_raw = obtener_permisos_usuario(request.user)

        # Roles disponibles para selección de vista previa (solo Super Admin)
        preview_roles = []
        if es_super_admin(request.user):
            try:
                from .models import Rol
                preview_roles = list(Rol.objects.filter(activo=True))
            except Exception:
                preview_roles = []
        return {
            'user_permissions': permisos_raw,
            'permisos': convertir_permisos_para_template(permisos_raw),
            'user_roles': [ur.rol for ur in obtener_roles_usuario(request.user)],
            'is_super_admin': es_super_admin(request.user),
            'role_preview_active': preview_role is not None,
            'role_preview_role': preview_role,
            'role_preview_roles': preview_roles,
        }
    return {}
