from django.urls import path
from . import views

app_name = 'admin'

urlpatterns = [
    # Usuarios
    path("usuarios/", views.usuarios_list, name="usuarios_list"),
    path("usuarios/<int:user_id>/", views.usuario_detail, name="usuario_detail"),
    path('reservas/activar/<int:reserva_id>/', views.activar_reserva, name='activar_reserva'),
    # Dashboard en /admin/
    path("", views.dashboard, name="dashboard"),

    # Empleados
    path("empleados/", views.empleados_list, name="empleados_list"),
    path("empleados/nuevo/", views.empleados_create, name="empleados_create"),
    path("empleados/editar/<int:pk>/", views.empleados_edit, name="empleados_edit"),
    path("empleados/eliminar/<int:pk>/", views.empleados_delete, name="empleados_delete"),

    # Planes
    path("planes/", views.planes_list, name="planes_list"),
    path("planes/nuevo/", views.planes_create, name="planes_create"),
    path("planes/editar/<int:pk>/", views.planes_edit, name="planes_edit"),
    path("planes/eliminar/<int:pk>/", views.planes_delete, name="planes_delete"),

    # Promociones
    path("promociones/", views.promociones_list, name="promociones_list"),
    path("promociones/nuevo/", views.promociones_create, name="promociones_create"),
    path("promociones/editar/<int:pk>/", views.promociones_edit, name="promociones_edit"),
    path("promociones/eliminar/<int:pk>/", views.promociones_delete, name="promociones_delete"),

    # Servicios
    path("servicios/", views.servicios_list, name="servicios_list"),
    path("servicios/nuevo/", views.servicios_create, name="servicios_create"),
    path("servicios/editar/<int:pk>/", views.servicios_edit, name="servicios_edit"),
    path("servicios/eliminar/<int:pk>/", views.servicios_delete, name="servicios_delete"),

    # Huéspedes
    path("huespedes/", views.huespedes_list, name="huespedes_list"),
    path("huespedes/nuevo/", views.huespedes_create, name="huespedes_create"),
    path("huespedes/editar/<int:pk>/", views.huespedes_edit, name="huespedes_edit"),
    path("huespedes/eliminar/<int:pk>/", views.huespedes_delete, name="huespedes_delete"),

    path('ver-reservas/', views.ver_reservas, name='ver_reservas'),
        # acciones sobre reservas (confirmar / rechazar)
    path('reservas/confirmar/<int:reserva_id>/', views.confirmar_reserva_admin, name='confirmar_reserva_admin'),
    path('reservas/rechazar/<int:reserva_id>/', views.rechazar_reserva_admin, name='rechazar_reserva_admin'),

    # listado y control de huéspedes activos
    path('huespedes-activos/', views.huespedes_activos, name='huespedes_activos'),
    path('huespedes-activos/finalizar/<int:activo_id>/', views.finalizar_huesped_activo, name='finalizar_huesped_activo'),

]
