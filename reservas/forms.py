from django import forms
from reservas.models import Reserva

class SeleccionarServicioForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ['servicios']  # <- plural, no 'servicio'
        widgets = {
            'servicios': forms.CheckboxSelectMultiple,
        }
