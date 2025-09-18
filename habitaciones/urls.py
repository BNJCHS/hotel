from django.urls import path
from . import views

app_name = 'habitaciones'

urlpatterns = [
    path('', views.lista_habitaciones_publica, name='list_habitaciones_reserva'),
    path('<int:id>/', views.detalle_habitacion_publica, name='detalle_habitacion_publica'),
    path('admin/habitaciones/', views.admin_habitaciones_list, name='habitaciones_list'),
    path('admin/habitaciones/nueva/', views.admin_habitaciones_create, name='habitaciones_create'),
    path('admin/habitaciones/<int:pk>/editar/', views.admin_habitaciones_edit, name='habitaciones_edit'),
    path('admin/habitaciones/<int:pk>/eliminar/', views.admin_habitaciones_delete, name='habitaciones_delete'),
    
    

]
