# administracion/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'), 
    path('habitaciones/', views.lista_habitaciones_admin, name='lista_habitaciones_admin'),
    path('habitaciones/<int:id>/', views.detalle_habitacion_admin, name='detalle_habitacion_admin'),
    path('habitaciones/crear/', views.crear_habitacion, name='crear_habitacion'),
    path('habitaciones/<int:id>/editar/', views.editar_habitacion, name='editar_habitacion'),
    path('habitaciones/<int:id>/eliminar/', views.eliminar_habitacion, name='eliminar_habitacion'),
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Clientes
    path('clientes/', views.clientes_list, name='clientes_list'),
    path('clientes/nuevo/', views.cliente_create, name='cliente_create'),
    path('clientes/<int:pk>/editar/', views.cliente_edit, name='cliente_edit'),
    
    # Huéspedes
    path('huespedes/', views.huespedes_list, name='huespedes_list'),
    path('huespedes/nuevo/', views.huesped_create, name='huesped_create'),
    path('huespedes/<int:pk>/editar/', views.huesped_edit, name='huesped_edit'),
    
    # Servicios
    path('servicios/', views.servicios_list, name='servicios_list'),
    path('servicios/nuevo/', views.servicio_create, name='servicio_create'),
    path('servicios/<int:pk>/editar/', views.servicio_edit, name='servicio_edit'),
    path('servicios/<int:pk>/toggle/', views.toggle_servicio_disponibilidad, name='toggle_servicio'),
    
    # Empleados
    path('empleados/', views.empleados_list, name='empleados_list'),
    path('empleados/nuevo/', views.empleado_create, name='empleado_create'),
    path('empleados/<int:pk>/editar/', views.empleado_edit, name='empleado_edit'),
    
    # Planes de Hospedaje
    path('planes/', views.planes_list, name='planes_list'),
    path('planes/nuevo/', views.plan_create, name='plan_create'),
    path('planes/<int:pk>/editar/', views.plan_edit, name='plan_edit'),
    
    # Promociones
    path('promociones/', views.promociones_list, name='promociones_list'),
    path('promociones/nueva/', views.promocion_create, name='promocion_create'),
    path('promociones/<int:pk>/editar/', views.promocion_edit, name='promocion_edit'),
    
    # API Endpoints
    path('api/stats/', views.api_stats, name='api_stats'),
]
