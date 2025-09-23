from django import forms
from .models import Habitacion, TipoHabitacion

class HabitacionAdminForm(forms.ModelForm):
    class Meta:
        model = Habitacion
        fields = ['numero', 'tipo_habitacion', 'disponible', 'en_mantenimiento', 'observaciones']
        widgets = {
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }

class TipoHabitacionForm(forms.ModelForm):
    class Meta:
        model = TipoHabitacion
        fields = ['nombre', 'precio', 'capacidad', 'descripcion', 'imagen', 'stock_total', 'stock_disponible', 'activo']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4}),
            'precio': forms.NumberInput(attrs={'step': '0.01'}),
        }
