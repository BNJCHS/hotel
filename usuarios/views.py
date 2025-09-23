
from django.shortcuts import render, redirect
from django.contrib.auth import login,logout, update_session_auth_hash
from django.contrib.auth.models import User
from .forms import RegistroForm, ProfileForm, UserPreferencesForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.urls import reverse_lazy
from django.contrib import messages
def register(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            print("Formulario válido")  # <---
            user = form.save()
            login(request, user)
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
        preferences_form = UserPreferencesForm(request.POST, user_profile=profile)
        
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
            return redirect('profile')
            
        elif 'update_preferences' in request.POST and preferences_form.is_valid():
            # Actualizar preferencias
            profile.preferences = preferences_form.get_preferences_data()
            profile.save()
            
            messages.success(request, 'Preferencias actualizadas correctamente')
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)
        preferences_form = UserPreferencesForm(user_profile=profile)
    
    # Obtener reservas del usuario y calcular estadísticas
    try:
        from reservas.models import Reserva
        from django.db.models import Sum, Count, Q
        from decimal import Decimal
        from datetime import datetime, timedelta
        
        reservations = Reserva.objects.filter(usuario=request.user).order_by('-fecha_reserva')[:5]
        all_reservations = Reserva.objects.filter(usuario=request.user)
        
        # Calcular estadísticas
        stats = {
            'total_reservations': all_reservations.count(),
            'confirmed_reservations': all_reservations.filter(confirmada=True).count(),
            'pending_reservations': all_reservations.filter(confirmada=False).count(),
            'total_spent': all_reservations.filter(confirmada=True).aggregate(
                total=Sum('monto_total')
            )['total'] or Decimal('0'),
            'current_year_reservations': all_reservations.filter(
                fecha_reserva__year=datetime.now().year
            ).count(),
            'last_30_days_reservations': all_reservations.filter(
                fecha_reserva__gte=datetime.now() - timedelta(days=30)
            ).count(),
        }
        
        # Método de pago más usado
        payment_methods = all_reservations.filter(
            metodo_pago__isnull=False
        ).values('metodo_pago').annotate(
            count=Count('metodo_pago')
        ).order_by('-count')
        
        stats['favorite_payment_method'] = payment_methods.first()['metodo_pago'] if payment_methods else None
        
        # Promedio de gasto por reserva
        if stats['confirmed_reservations'] > 0:
            stats['average_spent'] = stats['total_spent'] / stats['confirmed_reservations']
        else:
            stats['average_spent'] = Decimal('0')
            
    except Exception as e:
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
    
    context = {
        'page_title': 'Mi Perfil - Hotel Elegante',
        'meta_description': 'Gestiona tu perfil, revisa tus reservas y configura tu cuenta en Hotel Elegante.',
        'reservations': reservations,
        'form': form,
        'preferences_form': preferences_form,
        'stats': stats,
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
            return redirect('profile')
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