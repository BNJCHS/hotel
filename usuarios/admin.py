from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from .models import Profile

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Perfil'
    fields = ('avatar', 'phone', 'address', 'city', 'country', 'is_blocked', 'block_reason', 'last_login_ip')
    readonly_fields = ('created_at', 'blocked_at', 'blocked_by')

class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active', 'user_status', 'date_joined', 'last_login', 'user_actions')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined', 'profile__is_blocked')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'profile__phone')
    ordering = ('-date_joined',)
    
    def user_status(self, obj):
        """Muestra el estado del usuario con colores"""
        if hasattr(obj, 'profile') and obj.profile.is_blocked:
            return format_html(
                '<span style="color: red; font-weight: bold;">🚫 Bloqueado</span>'
            )
        elif obj.is_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">✅ Activo</span>'
            )
        else:
            return format_html(
                '<span style="color: orange; font-weight: bold;">⚠️ Inactivo</span>'
            )
    user_status.short_description = 'Estado'
    
    def user_actions(self, obj):
        """Botones de acción para el usuario"""
        if hasattr(obj, 'profile'):
            if obj.profile.is_blocked:
                return format_html(
                    '<a class="button" href="{}">Desbloquear</a>',
                    reverse('usuarios:unblock_user', args=[obj.pk])
                )
            else:
                return format_html(
                    '<a class="button" href="{}">Bloquear</a>',
                    reverse('usuarios:block_user', args=[obj.pk])
                )
        return '-'
    user_actions.short_description = 'Acciones'
    
    def get_queryset(self, request):
        """Optimiza las consultas incluyendo el perfil"""
        return super().get_queryset(request).select_related('profile')

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'city', 'country', 'is_blocked', 'created_at', 'blocked_status')
    list_filter = ('is_blocked', 'created_at', 'city', 'country')
    search_fields = ('user__username', 'user__email', 'phone', 'city', 'country')
    readonly_fields = ('created_at', 'blocked_at', 'blocked_by')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('user', 'avatar', 'phone', 'address', 'city', 'country')
        }),
        ('Sistema de Bloqueo', {
            'fields': ('is_blocked', 'blocked_at', 'blocked_by', 'block_reason'),
            'classes': ('collapse',)
        }),
        ('Información Técnica', {
            'fields': ('last_login_ip', 'created_at', 'preferences'),
            'classes': ('collapse',)
        }),
    )
    
    def blocked_status(self, obj):
        """Muestra información detallada del bloqueo"""
        if obj.is_blocked:
            blocked_info = f"Bloqueado el {obj.blocked_at.strftime('%d/%m/%Y %H:%M')}"
            if obj.blocked_by:
                blocked_info += f" por {obj.blocked_by.username}"
            return format_html(
                '<span style="color: red; font-weight: bold;">{}</span>',
                blocked_info
            )
        return format_html(
            '<span style="color: green;">No bloqueado</span>'
        )
    blocked_status.short_description = 'Estado de Bloqueo'
    
    actions = ['block_selected_users', 'unblock_selected_users']
    
    def block_selected_users(self, request, queryset):
        """Acción para bloquear usuarios seleccionados"""
        count = 0
        for profile in queryset.filter(is_blocked=False):
            profile.block_user(request.user, "Bloqueado desde el panel de administración")
            count += 1
        
        if count:
            messages.success(request, f'{count} usuario(s) bloqueado(s) exitosamente.')
        else:
            messages.warning(request, 'No se encontraron usuarios para bloquear.')
    
    block_selected_users.short_description = "Bloquear usuarios seleccionados"
    
    def unblock_selected_users(self, request, queryset):
        """Acción para desbloquear usuarios seleccionados"""
        count = 0
        for profile in queryset.filter(is_blocked=True):
            profile.unblock_user()
            count += 1
        
        if count:
            messages.success(request, f'{count} usuario(s) desbloqueado(s) exitosamente.')
        else:
            messages.warning(request, 'No se encontraron usuarios bloqueados para desbloquear.')
    
    unblock_selected_users.short_description = "Desbloquear usuarios seleccionados"

# Desregistrar el UserAdmin por defecto y registrar el personalizado
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
