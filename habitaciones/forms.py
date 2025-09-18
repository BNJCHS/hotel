from django import forms
from .models import Habitacion

class HabitacionAdminForm(forms.ModelForm):
    class Meta:
        model = Habitacion
        fields = ['numero', 'tipo', 'precio', 'disponible', 'descripcion', 'imagen', 'stock', 'capacidad']
