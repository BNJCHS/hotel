# administracion/forms.py
from django import forms
from habitaciones.models import Habitacion

class HabitacionForm(forms.ModelForm):
    class Meta:
        model = Habitacion
        fields = ['numero', 'tipo', 'precio', 'descripcion', 'imagen']  # Acordate de ajustar esto a tu modelo
