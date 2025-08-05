from django import forms
from .models import Reserva

class SeleccionarServicioForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ['servicio']
        widgets = {
            'servicio': forms.RadioSelect
        }
