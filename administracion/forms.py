from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .models import Empleado, Plan, Promocion, Servicio, Huesped

class EmpleadoForm(forms.ModelForm):
    class Meta:
        model = Empleado
        fields = "__all__"

class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = "__all__"

class PromocionForm(forms.ModelForm):
    class Meta:
        model = Promocion
        fields = "__all__"
        widgets = {
            "fecha_inicio": forms.DateInput(attrs={"type": "date"}),
            "fecha_fin": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned = super().clean()
        fi = cleaned.get("fecha_inicio")
        ff = cleaned.get("fecha_fin")
        if fi and ff and ff < fi:
            raise ValidationError("La fecha de finalización no puede ser anterior a la fecha de inicio.")
        return cleaned

class ServicioForm(forms.ModelForm):
    class Meta:
        model = Servicio
        fields = "__all__"

class HuespedForm(forms.ModelForm):
    class Meta:
        model = Huesped
        fields = "__all__"


class AdminLoginForm(forms.Form):
    """Formulario específico para el login de administración"""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Usuario administrador',
            'autocomplete': 'username'
        }),
        label='Usuario'
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña',
            'autocomplete': 'current-password'
        }),
        label='Contraseña'
    )
    
    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)
    
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        if username is not None and password:
            self.user_cache = authenticate(
                self.request, 
                username=username, 
                password=password
            )
            
            if self.user_cache is None:
                raise forms.ValidationError(
                    "Usuario o contraseña incorrectos.",
                    code='invalid_login'
                )
            
            # Verificar que el usuario sea staff (administrador)
            if not self.user_cache.is_staff:
                raise forms.ValidationError(
                    "Este usuario no tiene permisos de administración.",
                    code='no_admin_permission'
                )
            
            # Verificar que la cuenta esté activa
            if not self.user_cache.is_active:
                raise forms.ValidationError(
                    "Esta cuenta está desactivada.",
                    code='inactive'
                )
        
        return self.cleaned_data
    
    def get_user(self):
        return self.user_cache

