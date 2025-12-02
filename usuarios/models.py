from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='profiles/', null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    preferences = models.JSONField(default=dict, blank=True, null=True)

    # Campos de 2FA
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_pending_code = models.CharField(max_length=6, blank=True, null=True)
    two_factor_last_sent_at = models.DateTimeField(blank=True, null=True)
    
    # Campos para el sistema de bloqueo
    is_blocked = models.BooleanField(default=False, verbose_name="Usuario bloqueado")
    blocked_at = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de bloqueo")
    blocked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='blocked_users', verbose_name="Bloqueado por")
    block_reason = models.TextField(blank=True, null=True, verbose_name="Razón del bloqueo")
    
    # Campos adicionales para estadísticas
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name="Fecha de registro")
    last_login_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name="Última IP")
    
    def __str__(self):
        return f"Perfil de {self.user.username}"
    
    def block_user(self, admin_user, reason=""):
        """Bloquea al usuario"""
        self.is_blocked = True
        self.blocked_at = timezone.now()
        self.blocked_by = admin_user
        self.block_reason = reason
        self.save()
    
    def unblock_user(self):
        """Desbloquea al usuario"""
        self.is_blocked = False
        self.blocked_at = None
        self.blocked_by = None
        self.block_reason = ""
        self.save()
    
    def can_make_reservations(self):
        """Verifica si el usuario puede hacer reservas"""
        return not self.is_blocked and self.user.is_active
    
    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuarios"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
