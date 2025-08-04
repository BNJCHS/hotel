from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_habitaciones_publica, name='lista_habitaciones'),
    path('<int:id>/', views.detalle_habitacion_publica, name='detalle_habitacion_publica'),

]
