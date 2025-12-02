# usuarios/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import CustomPasswordResetView, CustomPasswordResetDoneView, CustomPasswordResetConfirmView, CustomPasswordResetCompleteView

app_name = 'usuarios'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('register/', views.register, name='register'),
    path('perfil/', views.profile, name='profile'),
    path('cambiar-contraseña/', views.password_change, name='password_change'),
    path('logout/', views.logout_view, name='logout'),
    # Recuperación de contraseña
    path('recuperar-contraseña/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('recuperar-contraseña/enviado/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('recuperar-contraseña/confirmar/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('recuperar-contraseña/completo/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    # Sistema de bloqueo de usuarios (solo para admin)
    path('admin/block-user/<int:user_id>/', views.block_user, name='block_user'),
    path('admin/unblock-user/<int:user_id>/', views.unblock_user, name='unblock_user'),
    # 2FA
    path('2fa/activar/', views.enable_two_factor, name='enable_two_factor'),
    path('2fa/verificar/codigo/', views.two_factor_verify_page, name='verify_two_factor_page'),
    path('2fa/verificar/exito/', views.two_factor_success_page, name='verify_two_factor_success_page'),
    path('2fa/verificar/', views.verify_two_factor, name='verify_two_factor'),
    path('2fa/desactivar/', views.disable_two_factor, name='disable_two_factor'),
    # Notificaciones
    path('notificaciones/toggle/', views.toggle_notifications, name='toggle_notifications'),
]
