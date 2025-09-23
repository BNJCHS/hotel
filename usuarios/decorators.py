from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def user_not_blocked(view_func):
    """
    Decorador que verifica que el usuario no esté bloqueado antes de permitir hacer reservas
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Verificar si el usuario está autenticado
        if not request.user.is_authenticated:
            return redirect('usuarios:login')
        
        # Verificar si el usuario tiene perfil y si está bloqueado
        if hasattr(request.user, 'profile') and request.user.profile.is_blocked:
            messages.error(
                request, 
                f'Tu cuenta ha sido bloqueada. Razón: {request.user.profile.block_reason or "No especificada"}. '
                'Contacta al administrador para más información.'
            )
            return redirect('usuarios:profile')
        
        # Verificar si el usuario puede hacer reservas
        if hasattr(request.user, 'profile') and not request.user.profile.can_make_reservations():
            messages.error(
                request, 
                'No puedes realizar reservas en este momento. Contacta al administrador.'
            )
            return redirect('usuarios:profile')
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view

def require_login_and_not_blocked(view_func):
    """
    Decorador que combina login_required con user_not_blocked
    """
    return login_required(user_not_blocked(view_func))