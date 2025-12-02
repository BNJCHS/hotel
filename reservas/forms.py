from django import forms
from reservas.models import Reserva, Huesped
from django.forms import modelformset_factory, BaseModelFormSet

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
        widgets = {
            'nombre': forms.TextInput(attrs={'required': True}),
            'apellido': forms.TextInput(attrs={'required': True}),
            'edad': forms.NumberInput(attrs={'required': True, 'min': 0}),
            'genero': forms.Select(attrs={'required': True}),
            'dni': forms.TextInput(attrs={'required': True}),
        }

class RequiredHuespedFormSet(BaseModelFormSet):
    """Formset que obliga a completar todos los formularios (sin permitir vacíos)."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for form in self.forms:
            form.empty_permitted = False

# Mantener export opcional (no usado en vistas actuales)
HuespedFormSet = modelformset_factory(Huesped, form=HuespedForm, extra=0)
