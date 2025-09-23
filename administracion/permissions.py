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
            if not usuario_tiene_permiso(request.user, modulo, accion):
                messages.error(
                    request, 
                    f'No tienes permisos para {accion} en el módulo {modulo}.'
                )
                if redirect_url:
                    return redirect(redirect_url)
                else:
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
            
            # Verificar que sea staff
            if not request.user.is_staff:
                messages.error(request, 'Acceso denegado. Se requieren permisos de staff.')
                return redirect('administracion:admin_login')
            
            # Verificar permisos específicos
            if not usuario_tiene_permiso(request.user, modulo, accion):
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
    
    class PermisosTemplate:
        def __init__(self, permisos_dict):
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
        permisos_raw = obtener_permisos_usuario(request.user)
        return {
            'user_permissions': permisos_raw,
            'permisos': convertir_permisos_para_template(permisos_raw),
            'user_roles': [ur.rol for ur in obtener_roles_usuario(request.user)],
            'is_super_admin': es_super_admin(request.user),
        }
    return {}
