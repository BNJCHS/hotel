from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .models import Empleado, Plan, Promocion, Servicio, Huesped
from reservas.models import Reserva


class BaseAdminModelForm(forms.ModelForm):
    """Aplica clases Bootstrap consistentes a todos los campos de formularios del área de administración."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            existing = widget.attrs.get('class', '')
            # Asignar clase según tipo de widget
            if isinstance(widget, forms.Select):
                class_name = 'form-select'
            elif isinstance(widget, forms.CheckboxInput):
                class_name = 'form-check-input'
            elif isinstance(widget, forms.RadioSelect):
                class_name = 'form-check-input'
            elif isinstance(widget, forms.CheckboxSelectMultiple):
                class_name = 'form-check-input'
            else:
                class_name = 'form-control'

            widget.attrs['class'] = f"{existing} {class_name}".strip()
            # Placeholder por defecto con la etiqueta del campo, si no existe
            widget.attrs.setdefault('placeholder', field.label or name.replace('_', ' ').title())
            # Marcar visualmente campos inválidos si hay errores
            if name in self.errors:
                widget.attrs['class'] = f"{widget.attrs['class']} is-invalid".strip()

class EmpleadoForm(BaseAdminModelForm):
    class Meta:
        model = Empleado
        fields = "__all__"

class PlanForm(BaseAdminModelForm):
    class Meta:
        model = Plan
        fields = "__all__"

class PromocionForm(BaseAdminModelForm):
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

class ServicioForm(BaseAdminModelForm):
    class Meta:
        model = Servicio
        fields = "__all__"

class HuespedForm(BaseAdminModelForm):
    class Meta:
        model = Huesped
        fields = "__all__"


class ReservaRapidaForm(BaseAdminModelForm):
    """Formulario simplificado para crear una reserva rápida desde administración."""
    class Meta:
        model = Reserva
        fields = [
            'tipo_habitacion',
            'cantidad_habitaciones',
            'plan',
            'promocion',
            'check_in',
            'check_out',
            'cantidad_huespedes',
        ]
        widgets = {
            'check_in': forms.DateInput(attrs={'type': 'date'}),
            'check_out': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned = super().clean()
        ci = cleaned.get('check_in')
        co = cleaned.get('check_out')
        if ci and co and co < ci:
            raise ValidationError('La fecha de salida no puede ser anterior a la fecha de entrada.')
        return cleaned


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

