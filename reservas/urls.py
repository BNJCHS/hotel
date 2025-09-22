from django.urls import path
from . import views

urlpatterns = [
    path('agregar/<int:habitacion_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('servicio/', views.seleccionar_servicio, name='seleccionar_servicio'),
    path('reserva_exitosa/', views.reserva_exitosa, name='reserva_exitosa'),
    path('mis/', views.mis_reservas, name='mis_reservas'),
    path('cancelar/<int:reserva_id>/', views.cancelar_reserva, name='cancelar_reserva'),
    path('servicio/agregar/', views.agregar_servicio, name='agregar_servicio'),
    path('fechas/', views.seleccionar_fechas, name='seleccionar_fechas'),
    path('seleccionar-huespedes/', views.seleccionar_huespedes, name='seleccionar_huespedes'),
    path("confirmar/<int:reserva_id>/", views.confirmar_reserva, name="confirmar_reserva"),
    path("confirmar/<str:token>/", views.confirmar_reserva_token, name="confirmar_reserva_token"),
    path('habitaciones/reservar/<int:habitacion_id>/', views.reservar_habitacion, name='reservar_habitacion'),
    path('detalle/<int:reserva_id>/', views.detalle_reserva, name='detalle_reserva'),
    # Nuevo: crear múltiples reservas a partir de una reserva base (sin chatbot)
    path('multiples/agregar/', views.agregar_reservas_multiples, name='agregar_reservas_multiples'),
]
