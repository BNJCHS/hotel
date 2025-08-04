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
]
