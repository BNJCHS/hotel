
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash, authenticate
from django.contrib.auth.models import User
from .forms import RegistroForm, ProfileForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import random

def register(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            print("Formulario válido")  # <---
            user = form.save()
            # Autenticar para establecer el backend y evitar el error con múltiples backends
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            authenticated_user = authenticate(request, username=username, password=raw_password)
            if authenticated_user is not None:
                login(request, authenticated_user)
            else:
                # En caso extremo, usar explícitamente el backend por defecto de Django
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('index')
        else:
            print("Formulario inválido")  # <---
            print(form.errors)  # Muestra errores
    else:
        form = RegistroForm()
    return render(request, 'register.html', {'form': form})


@login_required
def profile(request):
    """
    Vista del perfil del usuario
    """
    user = request.user
    
    # Verificar si el usuario tiene perfil, si no, crearlo
    try:
        profile = user.profile
    except:
        from .models import Profile
        profile = Profile.objects.create(user=user)
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        
        if 'update_profile' in request.POST and form.is_valid():
            # Actualizar datos del usuario
            user = request.user
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()
            
            # Actualizar perfil
            profile_form = form.save(commit=False)
            if 'avatar' in request.FILES:
                profile_form.avatar = request.FILES['avatar']
            profile_form.save()
            
            messages.success(request, 'Perfil actualizado correctamente')
            return redirect('usuarios:profile')
    else:
        form = ProfileForm(instance=profile)
    
    # Obtener reservas del usuario y calcular estadísticas
    try:
        from reservas.models import Reserva
        from django.db.models import Sum, Count
        from decimal import Decimal
        from datetime import timedelta
        from django.utils import timezone

        reservations = (
            Reserva.objects
            .filter(usuario=request.user)
            .select_related('tipo_habitacion', 'habitacion_asignada')
            .order_by('-fecha_reserva')
        )
        all_reservations = Reserva.objects.filter(usuario=request.user)

        # Calcular estadísticas con campos reales del modelo
        stats = {
            'total_reservations': all_reservations.count(),
            'confirmed_reservations': all_reservations.filter(estado='confirmada').count(),
            'pending_reservations': all_reservations.filter(estado='pendiente').count(),
            'total_spent': (
                all_reservations
                .filter(estado__in=['confirmada', 'completada'])
                .aggregate(total=Sum('monto'))
            )['total'] or Decimal('0'),
            'current_year_reservations': all_reservations.filter(
                fecha_reserva__year=timezone.now().year
            ).count(),
            'last_30_days_reservations': all_reservations.filter(
                fecha_reserva__gte=timezone.now() - timedelta(days=30)
            ).count(),
        }

        # Método de pago más usado
        payment_methods = (
            all_reservations
            .filter(metodo_pago__isnull=False)
            .values('metodo_pago')
            .annotate(count=Count('metodo_pago'))
            .order_by('-count')
        )
        stats['favorite_payment_method'] = payment_methods.first()['metodo_pago'] if payment_methods else None

        # Promedio de gasto por reserva
        if stats['confirmed_reservations'] > 0:
            stats['average_spent'] = stats['total_spent'] / stats['confirmed_reservations']
        else:
            stats['average_spent'] = Decimal('0')

    except Exception:
        # Si hay algún error (tabla no existe, etc.), simplemente no mostramos reservas
        reservations = []
        stats = {
            'total_reservations': 0,
            'confirmed_reservations': 0,
            'pending_reservations': 0,
            'total_spent': Decimal('0'),
            'current_year_reservations': 0,
            'last_30_days_reservations': 0,
            'favorite_payment_method': None,
            'average_spent': Decimal('0'),
        }
    
    # Estado actual de notificaciones (desde JSON preferences)
    try:
        prefs = profile.preferences or {}
    except Exception:
        prefs = {}
    notifications_enabled = prefs.get('notifications_enabled', True)
    
    context = {
        'page_title': 'Mi Perfil - Hotel Elegante',
        'meta_description': 'Gestiona tu perfil, revisa tus reservas y configura tu cuenta en Hotel Elegante.',
        'reservations': reservations,
        'form': form,
        'stats': stats,
        'notifications_enabled': notifications_enabled,
    }
    return render(request, 'perfil.html', context)

@login_required
def password_change(request):
    """
    Vista para cambiar la contraseña del usuario
    """
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Tu contraseña ha sido cambiada exitosamente.')
            return redirect('usuarios:profile')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        form = PasswordChangeForm(request.user)
    
    context = {
        'form': form,
        'page_title': 'Cambiar Contraseña - Hotel Elegante',
        'meta_description': 'Cambia tu contraseña de forma segura en Hotel Elegante.',
    }
    return render(request, 'password_change.html', context)

def logout_view(request):
    """
    Vista para cerrar sesión del usuario
    """
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente.')
    return redirect('index')

class CustomPasswordResetView(PasswordResetView):
    template_name = 'password_reset.html'
    email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Recuperar Contraseña - Hotel Elegante'
        context['meta_description'] = 'Recupera tu contraseña de Hotel Elegante de forma segura.'
        return context

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'password_reset_done.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Email Enviado - Hotel Elegante'
        context['meta_description'] = 'Te hemos enviado las instrucciones para recuperar tu contraseña.'
        return context

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Nueva Contraseña - Hotel Elegante'
        context['meta_description'] = 'Establece tu nueva contraseña para Hotel Elegante.'
        return context

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'password_reset_complete.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Contraseña Restablecida - Hotel Elegante'
        context['meta_description'] = 'Tu contraseña ha sido restablecida exitosamente.'
        return context

# Vistas para el sistema de bloqueo de usuarios (solo para administradores)
@login_required
@user_passes_test(lambda u: u.is_staff)
def block_user(request, user_id):
    """
    Vista para bloquear un usuario (solo para administradores)
    """
    try:
        user = User.objects.get(id=user_id)
        profile = user.profile
        
        if request.method == 'POST':
            reason = request.POST.get('reason', 'Bloqueado desde el panel de administración')
            profile.block_user(request.user, reason)
            messages.success(request, f'Usuario {user.username} bloqueado exitosamente.')
            return redirect('admin:auth_user_changelist')
        
        context = {
            'user_to_block': user,
            'page_title': f'Bloquear Usuario: {user.username}',
        }
        return render(request, 'admin/block_user.html', context)
        
    except User.DoesNotExist:
        messages.error(request, 'Usuario no encontrado.')
        return redirect('admin:auth_user_changelist')

@login_required
@user_passes_test(lambda u: u.is_staff)
def unblock_user(request, user_id):
    """
    Vista para desbloquear un usuario (solo para administradores)
    """
    try:
        user = User.objects.get(id=user_id)
        profile = user.profile
        
        if profile.is_blocked:
            profile.unblock_user()
            messages.success(request, f'Usuario {user.username} desbloqueado exitosamente.')
        else:
            messages.warning(request, f'El usuario {user.username} no estaba bloqueado.')
        
        return redirect('admin:auth_user_changelist')
        
    except User.DoesNotExist:
        messages.error(request, 'Usuario no encontrado.')
        return redirect('admin:auth_user_changelist')

# ===== VISTAS 2FA =====
@login_required
def enable_two_factor(request):
    if request.method == 'POST':
        profile = request.user.profile
        code = f"{random.randint(0, 999999):06d}"
        profile.two_factor_pending_code = code
        profile.two_factor_enabled = False
        profile.two_factor_last_sent_at = timezone.now()
        profile.save()
        # Enviar email con el código si hay email
        if request.user.email:
            try:
                send_mail(
                    subject='Código de verificación 2FA - Hotel Elegante',
                    message=f'Tu código de verificación es: {code}',
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                    recipient_list=[request.user.email],
                    fail_silently=True,
                )
                messages.info(request, 'Te enviamos un código a tu correo.')
            except Exception:
                messages.warning(request, 'No se pudo enviar el email. Ingresa el código mostrado si aplica.')
        else:
            messages.warning(request, 'No tienes email configurado. Contacta soporte para completar 2FA.')
        return redirect('usuarios:verify_two_factor_page')
    return redirect('usuarios:profile')

@login_required
def two_factor_verify_page(request):
    profile = request.user.profile
    if not profile.two_factor_pending_code:
        messages.info(request, 'No tienes una verificación 2FA pendiente.')
        return redirect('usuarios:profile')
    context = {
        'page_title': 'Verificar 2FA - Hotel Elegante',
        'meta_description': 'Introduce el código para activar la autenticación de dos factores.',
    }
    return render(request, 'two_factor_verify.html', context)

@login_required
def verify_two_factor(request):
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        profile = request.user.profile
        if code and profile.two_factor_pending_code and code == profile.two_factor_pending_code:
            profile.two_factor_enabled = True
            profile.two_factor_pending_code = ''
            profile.save()
            messages.success(request, 'Autenticación de dos factores activada.')
            return redirect('usuarios:verify_two_factor_success_page')
        else:
            messages.error(request, 'Código incorrecto o expirado. Intenta nuevamente.')
            return redirect('usuarios:verify_two_factor_page')
    return redirect('usuarios:profile')

@login_required
def two_factor_success_page(request):
    profile = request.user.profile
    if not profile.two_factor_enabled:
        messages.info(request, 'Aún no has activado 2FA. Ingresa el código para completarlo.')
        return redirect('usuarios:verify_two_factor_page')
    context = {
        'page_title': '2FA Activada - Hotel Elegante',
        'meta_description': 'Confirmación de activación de la autenticación de dos factores.',
    }
    return render(request, 'two_factor_success.html', context)

@login_required
def disable_two_factor(request):
    if request.method == 'POST':
        profile = request.user.profile
        profile.two_factor_enabled = False
        profile.two_factor_pending_code = ''
        profile.save()
        messages.success(request, 'Autenticación de dos factores desactivada.')
        return redirect('usuarios:profile')
    return redirect('usuarios:profile')


@login_required
def toggle_notifications(request):
    """Actualiza la preferencia de notificaciones del perfil del usuario."""
    if request.method == 'POST':
        user = request.user
        try:
            profile = user.profile
        except Exception:
            from .models import Profile
            profile = Profile.objects.create(user=user)
        
        prefs = profile.preferences or {}
        new_value = request.POST.get('notifications_enabled')
        enabled = new_value == 'on' or new_value == 'true' or new_value == '1'
        prefs['notifications_enabled'] = enabled
        profile.preferences = prefs
        profile.save()
        
        if enabled:
            messages.success(request, 'Has activado las notificaciones y promociones por email.')
        else:
            messages.info(request, 'Has desactivado las notificaciones y promociones por email.')
        return redirect('usuarios:profile')
    
    messages.error(request, 'Solicitud inválida.')
    return redirect('usuarios:profile')
