from django.urls import path
from . import views

urlpatterns = [
    path('carrito/', views.ver_carrito, name='ver_carrito'),
    path('agregar/<int:habitacion_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('servicio/<int:reserva_id>/', views.seleccionar_servicio, name='seleccionar_servicio'),
]
