from django import forms
from .models import Habitacion, TipoHabitacion

class HabitacionAdminForm(forms.ModelForm):
    class Meta:
        model = Habitacion
        fields = ['numero', 'tipo', 'precio', 'disponible', 'descripcion', 'imagen', 'stock', 'capacidad']

class TipoHabitacionForm(forms.ModelForm):
    class Meta:
        model = TipoHabitacion
        fields = ['nombre', 'precio', 'capacidad', 'descripcion', 'imagen']
