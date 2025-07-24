from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('reservar/<int:habitacion_id>/', views.reservar, name='reservar'),
    path('buscar/', views.buscar_habitaciones, name='buscar_habitaciones'),
]
