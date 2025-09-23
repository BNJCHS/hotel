from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile
import json

class RegistroForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=False)
    
    class Meta:
        model = Profile
        fields = ['phone', 'address', 'city', 'country', 'avatar']
        
    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

class UserPreferencesForm(forms.Form):
    # Preferencias de notificaciones
    email_notifications = forms.BooleanField(
        required=False,
        label="Recibir notificaciones por email",
        help_text="Recibir confirmaciones de reserva y actualizaciones por email"
    )
    sms_notifications = forms.BooleanField(
        required=False,
        label="Recibir notificaciones por SMS",
        help_text="Recibir recordatorios y confirmaciones por SMS"
    )
    marketing_emails = forms.BooleanField(
        required=False,
        label="Recibir ofertas y promociones",
        help_text="Recibir información sobre ofertas especiales y promociones"
    )
    
    # Preferencias de habitación
    room_type_preference = forms.ChoiceField(
        choices=[
            ('', 'Sin preferencia'),
            ('individual', 'Individual'),
            ('doble', 'Doble'),
            ('suite', 'Suite'),
            ('familiar', 'Familiar'),
        ],
        required=False,
        label="Tipo de habitación preferida"
    )
    floor_preference = forms.ChoiceField(
        choices=[
            ('', 'Sin preferencia'),
            ('bajo', 'Pisos bajos (1-3)'),
            ('medio', 'Pisos medios (4-7)'),
            ('alto', 'Pisos altos (8+)'),
        ],
        required=False,
        label="Preferencia de piso"
    )
    view_preference = forms.ChoiceField(
        choices=[
            ('', 'Sin preferencia'),
            ('ciudad', 'Vista a la ciudad'),
            ('mar', 'Vista al mar'),
            ('montaña', 'Vista a la montaña'),
            ('jardin', 'Vista al jardín'),
        ],
        required=False,
        label="Preferencia de vista"
    )
    
    # Preferencias de servicios
    breakfast_included = forms.BooleanField(
        required=False,
        label="Incluir desayuno por defecto",
        help_text="Agregar automáticamente el desayuno a las reservas"
    )
    late_checkout = forms.BooleanField(
        required=False,
        label="Solicitar checkout tardío",
        help_text="Solicitar automáticamente checkout tardío cuando esté disponible"
    )
    early_checkin = forms.BooleanField(
        required=False,
        label="Solicitar checkin temprano",
        help_text="Solicitar automáticamente checkin temprano cuando esté disponible"
    )
    
    # Preferencias de pago
    preferred_payment_method = forms.ChoiceField(
        choices=[
            ('', 'Sin preferencia'),
            ('efectivo', 'Efectivo'),
            ('credito', 'Tarjeta de Crédito'),
            ('debito', 'Tarjeta de Débito'),
            ('mercadopago', 'MercadoPago'),
            ('paypal', 'PayPal'),
            ('transferencia', 'Transferencia Bancaria'),
        ],
        required=False,
        label="Método de pago preferido"
    )
    
    # Preferencias de idioma y moneda
    language_preference = forms.ChoiceField(
        choices=[
            ('es', 'Español'),
            ('en', 'English'),
            ('pt', 'Português'),
            ('fr', 'Français'),
        ],
        required=False,
        label="Idioma preferido"
    )
    currency_preference = forms.ChoiceField(
        choices=[
            ('ARS', 'Peso Argentino (ARS)'),
            ('USD', 'Dólar Estadounidense (USD)'),
            ('EUR', 'Euro (EUR)'),
            ('BRL', 'Real Brasileño (BRL)'),
        ],
        required=False,
        label="Moneda preferida"
    )
    
    def __init__(self, *args, **kwargs):
        user_profile = kwargs.pop('user_profile', None)
        super().__init__(*args, **kwargs)
        
        if user_profile and user_profile.preferences:
            prefs = user_profile.preferences
            for field_name in self.fields:
                if field_name in prefs:
                    self.fields[field_name].initial = prefs[field_name]
    
    def get_preferences_data(self):
        """Retorna los datos del formulario como diccionario para almacenar en JSON"""
        return {field: value for field, value in self.cleaned_data.items()}
