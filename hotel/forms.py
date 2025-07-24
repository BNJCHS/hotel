from django import forms
from .models import Reserva, Cliente
from django.core.exceptions import ValidationError
from datetime import date

class ReservaForm(forms.ModelForm):
    nombre = forms.CharField(max_length=100, required=True)
    apellido = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    telefono = forms.CharField(max_length=20, required=False)

    class Meta:
        model = Reserva
        fields = ['fecha_entrada', 'fecha_salida']

    def clean(self):
        cleaned_data = super().clean()
        entrada = cleaned_data.get("fecha_entrada")
        salida = cleaned_data.get("fecha_salida")

        if entrada and salida:
            if entrada < date.today():
                raise ValidationError("La fecha de entrada no puede ser anterior a hoy.")
            if salida <= entrada:
                raise ValidationError("La fecha de salida debe ser posterior a la fecha de entrada.")
        return cleaned_data
