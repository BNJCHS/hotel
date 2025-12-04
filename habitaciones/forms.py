from django import forms
from .models import Habitacion, TipoHabitacion


class BaseAdminModelForm(forms.ModelForm):
    """Aplica clases Bootstrap a los formularios de habitaciones usados en administración."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            existing = widget.attrs.get('class', '')
            if isinstance(widget, forms.Select):
                class_name = 'form-select'
            elif isinstance(widget, forms.CheckboxInput):
                class_name = 'form-check-input'
            elif isinstance(widget, forms.RadioSelect):
                class_name = 'form-check-input'
            elif isinstance(widget, forms.CheckboxSelectMultiple):
                class_name = 'form-check-input'
            else:
                class_name = 'form-control'
            widget.attrs['class'] = f"{existing} {class_name}".strip()
            widget.attrs.setdefault('placeholder', field.label or name.replace('_', ' ').title())
            if name in self.errors:
                widget.attrs['class'] = f"{widget.attrs['class']} is-invalid".strip()

class HabitacionAdminForm(BaseAdminModelForm):
    class Meta:
        model = Habitacion
        fields = ['numero', 'tipo_habitacion', 'disponible', 'en_mantenimiento', 'observaciones']
        widgets = {
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }

class TipoHabitacionForm(BaseAdminModelForm):
    TIPO_CHOICES = [
        ('simple', 'simple'),
        ('doble', 'doble'),
        ('familiar1', 'familiar1'),
        ('familiar2', 'familiar2'),
        ('familiar 3', 'familiar 3'),
        ('suite', 'suite'),
        ('suite premiun', 'suite premiun'),
        ('suite precidencia', 'suite precidencia'),
    ]

    nombre = forms.ChoiceField(choices=TIPO_CHOICES, label='Tipo')

    class Meta:
        model = TipoHabitacion
        fields = ['nombre', 'precio', 'capacidad', 'descripcion', 'imagen', 'stock_total', 'activo']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4}),
            'precio': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.pk:
            try:
                prev = TipoHabitacion.objects.get(pk=instance.pk)
                delta = int(instance.stock_total) - int(prev.stock_total)
                nuevo_disponible = int(prev.stock_disponible) + delta
                if nuevo_disponible < 0:
                    nuevo_disponible = 0
                if nuevo_disponible > int(instance.stock_total):
                    nuevo_disponible = int(instance.stock_total)
                instance.stock_disponible = nuevo_disponible
            except TipoHabitacion.DoesNotExist:
                instance.stock_disponible = instance.stock_total
        else:
            instance.stock_disponible = instance.stock_total
        if commit:
            instance.save()
        return instance
