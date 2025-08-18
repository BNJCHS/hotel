
from django.shortcuts import render, redirect
from django.contrib.auth import login,logout
from .forms import RegistroForm
from django.contrib.auth.decorators import login_required
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
    if request.method == 'POST':
        # Procesar actualización del perfil
        user = request.user
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        user.email = request.POST.get('email', '').strip()
        user.save()
        context = {
            'success': 'Perfil actualizado correctamente',
            'page_title': 'Mi Perfil - Hotel Elegante',
            'reservations': [],  # En una app real, obtener reservas del usuario
        }
        return render(request, 'perfil.html', context)
    
    # Obtener reservas del usuario (simulado)
    # En una app real: reservations = Reservation.objects.filter(user=request.user).order_by('-created_at')[:5]
    reservations = []
    
    context = {
        'page_title': 'Mi Perfil - Hotel Elegante',
        'meta_description': 'Gestiona tu perfil, revisa tus reservas y configura tu cuenta en Hotel Elegante.',
        'reservations': reservations,
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