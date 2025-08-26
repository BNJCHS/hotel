from django import forms
from django.core.exceptions import ValidationError
from .models import Empleado, Plan, Promocion, Servicio, Huesped

class EmpleadoForm(forms.ModelForm):
    class Meta:
        model = Empleado
        fields = "__all__"

class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = "__all__"

class PromocionForm(forms.ModelForm):
    class Meta:
        model = Promocion
        fields = "__all__"
        widgets = {
            "fecha_inicio": forms.DateInput(attrs={"type": "date"}),
            "fecha_fin": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned = super().clean()
        fi = cleaned.get("fecha_inicio")
        ff = cleaned.get("fecha_fin")
        if fi and ff and ff < fi:
            raise ValidationError("La fecha de finalización no puede ser anterior a la fecha de inicio.")
        return cleaned

class ServicioForm(forms.ModelForm):
    class Meta:
        model = Servicio
        fields = "__all__"

class HuespedForm(forms.ModelForm):
    class Meta:
        model = Huesped
        fields = "__all__"

