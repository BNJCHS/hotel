from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('sobre-nosotros/', views.about, name='about'),
    path('contacto/', views.contact, name='contact'),
    path('api/check-availability/', views.check_availability, name='check_availability'),
    path('api/contact/', views.contact_form, name='contact_form'),
    path('plan/<int:plan_id>/', views.detalle_plan, name='detalle_plan'),
    path('promocion/<int:promocion_id>/', views.promocion_detalle, name='promocion_detalle'),
    path('servicio/<int:servicio_id>/', views.servicio_detalle, name='servicio_detalle'),
    path("planes/", views.planes_list, name="planes_lista"),
    path("promociones/", views.promociones_list, name="promociones_lista"),
    path("reservar/plan/<int:plan_id>/", views.reservar_plan, name="reservar_plan"),
    path("reservar/promocion/<int:promocion_id>/", views.reservar_promocion, name="reservar_promocion"),
    path('habitaciones/', views.lista_habitaciones, name='habitaciones_lista'),
    path('habitacion/<int:id>/', views.habitacion_detalle, name='habitacion_detalle'),
    path('planes-promociones/', views.planes_y_promociones, name='planes_y_promociones'),
    path('reservar/plan/<int:plan_id>/', views.reservar_plan, name='reservar_plan'),
    path('reservar/promocion/<int:promocion_id>/', views.reservar_promocion, name='reservar_promocion'),
]

