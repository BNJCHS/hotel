from django.urls import path
from . import views

app_name = 'administracion'

urlpatterns = [
    # Autenticación específica para administración
    path("login/", views.admin_login, name="admin_login"),
    path("logout/", views.admin_logout, name="admin_logout"),
    
    # Dashboard en /admin/
    path("", views.dashboard, name="dashboard"),
    
    # Usuarios
    path("usuarios/", views.usuarios_list, name="usuarios_list"),
    path("usuarios/<int:user_id>/", views.usuario_detail, name="usuario_detail"),
    path("usuarios/<int:user_id>/bloquear/", views.block_user, name="block_user"),
    path("usuarios/<int:user_id>/desbloquear/", views.unblock_user, name="unblock_user"),
    path('reservas/activar/<int:reserva_id>/', views.activar_reserva, name='activar_reserva'),


    # Planes
    path("planes/", views.planes_list, name="planes_list"),
    path("planes/nuevo/", views.planes_create, name="planes_create"),
    path("planes/editar/<int:pk>/", views.planes_edit, name="planes_edit"),
    path("planes/eliminar/<int:pk>/", views.planes_delete, name="planes_delete"),
    path("planes/enviar/<int:pk>/", views.planes_send_email, name="planes_send_email"),
    path("planes/previsualizar/<int:pk>/", views.planes_preview_email, name="planes_preview_email"),

    # Promociones
    path("promociones/", views.promociones_list, name="promociones_list"),
    path("promociones/nuevo/", views.promociones_create, name="promociones_create"),
    path("promociones/editar/<int:pk>/", views.promociones_edit, name="promociones_edit"),
    path("promociones/eliminar/<int:pk>/", views.promociones_delete, name="promociones_delete"),
    path("promociones/enviar/<int:pk>/", views.promociones_send_email, name="promociones_send_email"),
    path("promociones/previsualizar/<int:pk>/", views.promociones_preview_email, name="promociones_preview_email"),

    # Servicios
    path("servicios/", views.servicios_list, name="servicios_list"),
    path("servicios/nuevo/", views.servicios_create, name="servicios_create"),
    path("servicios/editar/<int:pk>/", views.servicios_edit, name="servicios_edit"),
    path("servicios/eliminar/<int:pk>/", views.servicios_delete, name="servicios_delete"),

    # Huéspedes
    path("huespedes/", views.huespedes_list, name="huespedes_list"),
    path("huespedes/detalle/<int:pk>/", views.huesped_detail, name="huesped_detail"),
    path("huespedes/nuevo/", views.huespedes_create, name="huespedes_create"),
    path("huespedes/editar/<int:pk>/", views.huespedes_edit, name="huespedes_edit"),
    path("huespedes/eliminar/<int:pk>/", views.huespedes_delete, name="huespedes_delete"),

    path('ver-reservas/', views.ver_reservas, name='ver_reservas'),
    path('reservas/nueva/', views.reserva_rapida_create, name='reservas_nueva'),
        # acciones sobre reservas (confirmar / rechazar)
    path('reservas/confirmar/<int:reserva_id>/', views.confirmar_reserva_admin, name='confirmar_reserva_admin'),
    path('reservas/rechazar/<int:reserva_id>/', views.rechazar_reserva_admin, name='rechazar_reserva_admin'),
    path('reservas/finalizar/<int:reserva_id>/', views.finalizar_reserva_admin, name='finalizar_reserva_admin'),

    # listado y control de huéspedes activos
    path('huespedes-activos/', views.huespedes_activos, name='huespedes_activos'),
    path('huespedes-activos/finalizar/<int:activo_id>/', views.finalizar_huesped_activo, name='finalizar_huesped_activo'),

    # Gestión de roles y permisos
    path('roles/', views.roles_list, name='roles_list'),
    path('roles/nuevo/', views.roles_create, name='roles_create'),
    path('roles/editar/<int:pk>/', views.roles_edit, name='roles_edit'),
    path('roles/eliminar/<int:pk>/', views.roles_delete, name='roles_delete'),
    path('roles/asignar/', views.asignar_rol, name='asignar_rol'),
    path('roles/cambiar/', views.cambiar_rol, name='cambiar_rol'),
    path('roles/revocar/<int:asignacion_id>/', views.revocar_rol, name='revocar_rol'),

    # Vista como rol (solo Super Admin)
    path('roles/preview/set/', views.role_preview_set, name='role_preview_set'),
    path('roles/preview/clear/', views.role_preview_clear, name='role_preview_clear'),

]
