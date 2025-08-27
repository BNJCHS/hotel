from django import forms
from reservas.models import Reserva, Huesped

class SeleccionarServicioForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ['servicios']  # <- plural, no 'servicio'
        widgets = {
            'servicios': forms.CheckboxSelectMultiple,
        }

class HuespedForm(forms.ModelForm):
    class Meta:
        model = Huesped
        fields = ['nombre', 'apellido', 'edad', 'genero', 'dni']

from django.forms import modelformset_factory

HuespedFormSet = modelformset_factory(Huesped, form=HuespedForm, extra=0)
