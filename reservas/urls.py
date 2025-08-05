from django.urls import path
from . import views

urlpatterns = [
    path('agregar/<int:habitacion_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('servicio/', views.seleccionar_servicio, name='seleccionar_servicio'),
    path('reserva_exitosa/', views.reserva_exitosa, name='reserva_exitosa'),
    path('mis/', views.mis_reservas, name='mis_reservas'),
    path('cancelar/<int:reserva_id>/', views.cancelar_reserva, name='cancelar_reserva'),


]
