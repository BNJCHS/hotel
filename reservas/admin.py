from django.contrib import admin
from .models import Reserva, Huesped

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ['id', 'usuario', 'tipo_habitacion', 'cantidad_habitaciones', 'check_in', 'check_out', 'estado', 'precio_total', 'fecha_reserva']
    list_filter = ['estado', 'tipo_habitacion', 'check_in', 'check_out', 'fecha_reserva']
    search_fields = ['usuario__username', 'usuario__email', 'tipo_habitacion__nombre', 'token', 'codigo_checkin']
    readonly_fields = ['precio_total', 'fecha_reserva', 'token', 'codigo_checkin']
    
    fieldsets = (
        ('Información del Cliente', {
            'fields': ('usuario', 'cantidad_huespedes')
        }),
        ('Detalles de la Reserva', {
            'fields': ('tipo_habitacion', 'cantidad_habitaciones', 'habitacion_asignada')
        }),
        ('Fechas', {
            'fields': ('check_in', 'check_out', 'fecha_reserva')
        }),
        ('Servicios y Extras', {
            'fields': ('servicios', 'plan', 'promocion')
        }),
        ('Estado y Pago', {
            'fields': ('estado', 'metodo_pago', 'monto', 'precio_total')
        }),
        ('Sistema', {
            'fields': ('token', 'codigo_checkin'),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ['servicios']
    
    def precio_total(self, obj):
        return obj.precio_total()
    precio_total.short_description = 'Precio Total'
    
    actions = ['confirmar_reservas', 'cancelar_reservas']
    
    def confirmar_reservas(self, request, queryset):
        count = 0
        for reserva in queryset:
            if reserva.estado == 'pendiente':
                reserva.confirmar()
                count += 1
        self.message_user(request, f'{count} reservas confirmadas.')
    confirmar_reservas.short_description = 'Confirmar reservas seleccionadas'
    
    def cancelar_reservas(self, request, queryset):
        count = 0
        for reserva in queryset:
            if reserva.estado in ['pendiente', 'confirmada']:
                reserva.cancelar()
                count += 1
        self.message_user(request, f'{count} reservas canceladas.')
    cancelar_reservas.short_description = 'Cancelar reservas seleccionadas'

@admin.register(Huesped)
class HuespedAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'apellido', 'documento', 'reserva', 'fecha_nacimiento']
    list_filter = ['reserva__tipo_habitacion', 'reserva__check_in']
    search_fields = ['nombre', 'apellido', 'documento', 'email']
