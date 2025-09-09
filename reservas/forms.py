from django import forms
from reservas.models import Reserva, Huesped
from django.forms import modelformset_factory

class SeleccionarServicioForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ['servicios']  
        widgets = {
            'servicios': forms.CheckboxSelectMultiple(),  
        }

class HuespedForm(forms.ModelForm):
    class Meta:
        model = Huesped
        fields = ['nombre', 'apellido', 'edad', 'genero', 'dni']

HuespedFormSet = modelformset_factory(Huesped, form=HuespedForm, extra=0)
