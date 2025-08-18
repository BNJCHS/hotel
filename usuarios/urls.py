# usuarios/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import CustomPasswordResetView, CustomPasswordResetDoneView, CustomPasswordResetConfirmView, CustomPasswordResetCompleteView

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
]
