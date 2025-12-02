from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.conf import settings
from django.core.mail import EmailMessage
from .models import (
    Empleado, Plan, Promocion, Servicio, Huesped,
    Rol, Permiso, RolPermiso, UsuarioRol
)
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone


class RolPermisoInline(admin.TabularInline):
    model = RolPermiso
    extra = 0
    autocomplete_fields = ['permiso']


class UsuarioRolInline(admin.TabularInline):
    model = UsuarioRol
    fk_name = 'usuario'
    extra = 0
    autocomplete_fields = ['rol']
    readonly_fields = ['fecha_asignacion']


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ['get_nombre_display', 'nombre', 'activo', 'cantidad_usuarios', 'cantidad_permisos']
    list_filter = ['activo']
    search_fields = ['nombre', 'descripcion']
    inlines = [RolPermisoInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'descripcion', 'activo')
        }),
    )
    
    def get_nombre_display(self, obj):
        return obj.get_nombre_display()
    get_nombre_display.short_description = 'Nombre'
    
    def cantidad_usuarios(self, obj):
        count = UsuarioRol.objects.filter(rol=obj, activo=True).count()
        return format_html(
            '<span style="color: {};">{}</span>',
            'green' if count > 0 else 'gray',
            count
        )
    cantidad_usuarios.short_description = 'Usuarios'
    
    def cantidad_permisos(self, obj):
        count = RolPermiso.objects.filter(rol=obj).count()
        return format_html(
            '<span style="color: {};">{}</span>',
            'blue' if count > 0 else 'gray',
            count
        )
    cantidad_permisos.short_description = 'Permisos'


@admin.register(Permiso)
class PermisoAdmin(admin.ModelAdmin):
    list_display = ['descripcion', 'modulo', 'accion', 'cantidad_roles']
    list_filter = ['modulo', 'accion']
    search_fields = ['modulo', 'accion', 'descripcion']
    ordering = ['modulo', 'accion']
    
    def cantidad_roles(self, obj):
        count = RolPermiso.objects.filter(permiso=obj).count()
        return format_html(
            '<span style="color: {};">{}</span>',
            'blue' if count > 0 else 'gray',
            count
        )
    cantidad_roles.short_description = 'Roles'


@admin.register(UsuarioRol)
class UsuarioRolAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'rol', 'activo', 'fecha_asignacion', 'asignado_por']
    list_filter = ['activo', 'rol', 'fecha_asignacion']
    search_fields = ['usuario__username', 'usuario__first_name', 'usuario__last_name', 'rol__nombre']
    autocomplete_fields = ['usuario', 'rol', 'asignado_por']
    readonly_fields = ['fecha_asignacion']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('usuario', 'rol', 'asignado_por')


# Extender el UserAdmin para mostrar roles
class UserAdmin(BaseUserAdmin):
    inlines = BaseUserAdmin.inlines + (UsuarioRolInline,)
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)


# Re-registrar User con el nuevo admin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# Registrar modelos existentes
@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'apellido', 'dni', 'puesto', 'salario']
    list_filter = ['puesto']
    search_fields = ['nombre', 'apellido', 'dni']
    ordering = ['apellido', 'nombre']


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'precio', 'habitacion']
    list_filter = ['habitacion']
    search_fields = ['nombre', 'descripcion']
    actions = ['enviar_plan_por_email']

    def enviar_plan_por_email(self, request, queryset):
        """Envía el plan seleccionado por email a usuarios con notificaciones activadas (HTML + CTA)."""
        users = User.objects.filter(is_active=True).exclude(email="").select_related('profile')
        recipients = []
        for u in users:
            try:
                prefs = getattr(u.profile, 'preferences', {}) or {}
                if prefs.get('notifications_enabled', True):
                    recipients.append(u.email)
            except Exception:
                recipients.append(u.email)
        recipients = list(dict.fromkeys(recipients))
        if not recipients:
            self.message_user(request, 'No hay usuarios con notificaciones activadas o emails válidos.', level='warning')
            return
        enviados = 0
        today = timezone.now().date()
        for plan in queryset:
            subject = f"Plan: {plan.nombre}"
            plan_url = request.build_absolute_uri(reverse('detalle_plan', args=[plan.id]))
            imagen_url = request.build_absolute_uri(plan.imagen.url) if getattr(plan, 'imagen', None) else None

            html_body = render_to_string('emails/plan_email.html', {
                'plan': plan,
                'plan_url': plan_url,
                'imagen_url': imagen_url,
                'year': today.year,
            })
            text_body = strip_tags(html_body)
            try:
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    bcc=recipients,
                )
                email.attach_alternative(html_body, "text/html")
                email.send(fail_silently=False)
                enviados += 1
            except Exception as e:
                self.message_user(request, f'Error al enviar "{plan.nombre}": {e}', level='error')
        self.message_user(request, f"Planes enviados: {enviados}. Destinatarios: {len(recipients)} usuarios.")
    enviar_plan_por_email.short_description = 'Enviar plan por email a usuarios (respeta notificaciones)'


@admin.register(Promocion)
class PromocionAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descuento', 'fecha_inicio', 'fecha_fin', 'activa']
    list_filter = ['fecha_inicio', 'fecha_fin']
    search_fields = ['nombre', 'descripcion']
    actions = ['enviar_promocion_por_email']
    
    def activa(self, obj):
        from django.utils import timezone
        now = timezone.now().date()
        is_active = obj.fecha_inicio <= now <= obj.fecha_fin
        return format_html(
            '<span style="color: {};">{}</span>',
            'green' if is_active else 'red',
            'Sí' if is_active else 'No'
        )
    activa.short_description = 'Activa'

    def enviar_promocion_por_email(self, request, queryset):
        """Envía la promoción seleccionada por email a usuarios con notificaciones activadas (HTML + CTA)."""
        users = User.objects.filter(is_active=True).exclude(email="").select_related('profile')
        recipients = []
        for u in users:
            try:
                prefs = getattr(u.profile, 'preferences', {}) or {}
                if prefs.get('notifications_enabled', True):
                    recipients.append(u.email)
            except Exception:
                recipients.append(u.email)
        recipients = list(dict.fromkeys(recipients))
        if not recipients:
            self.message_user(request, 'No hay usuarios con notificaciones activadas o emails válidos.', level='warning')
            return
        enviados = 0
        today = timezone.now().date()
        for promo in queryset:
            subject = f"Promoción: {promo.nombre} ({promo.descuento}%)"
            is_active = promo.fecha_inicio <= today <= promo.fecha_fin
            estado = 'activa' if is_active else ('proxima' if today < promo.fecha_inicio else 'finalizada')
            dias_restantes = (promo.fecha_fin - today).days if is_active else 0
            dias_para_inicio = (promo.fecha_inicio - today).days if today < promo.fecha_inicio else 0
            promo_url = request.build_absolute_uri(reverse('promocion_detalle', args=[promo.id]))
            imagen_url = request.build_absolute_uri(promo.imagen.url) if getattr(promo, 'imagen', None) else None

            html_body = render_to_string('emails/promocion_email.html', {
                'promocion': promo,
                'estado': estado,
                'dias_restantes': dias_restantes,
                'dias_para_inicio': dias_para_inicio,
                'promo_url': promo_url,
                'imagen_url': imagen_url,
                'year': today.year,
            })
            text_body = strip_tags(html_body)
            try:
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    bcc=recipients,
                )
                email.attach_alternative(html_body, "text/html")
                email.send(fail_silently=False)
                enviados += 1
            except Exception as e:
                self.message_user(request, f'Error al enviar "{promo.nombre}": {e}', level='error')
        self.message_user(request, f"Promociones enviadas: {enviados}. Destinatarios: {len(recipients)} usuarios.")
    enviar_promocion_por_email.short_description = 'Enviar promoción por email a usuarios (respeta notificaciones)'


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'precio']
    search_fields = ['nombre', 'descripcion']
    ordering = ['nombre']


@admin.register(Huesped)
class HuespedAdmin(admin.ModelAdmin):
    list_display = ['apellido', 'nombre', 'dni', 'telefono', 'email']
    search_fields = ['nombre', 'apellido', 'dni', 'email']
    ordering = ['apellido', 'nombre']
