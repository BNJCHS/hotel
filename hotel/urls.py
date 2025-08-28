from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('sobre-nosotros/', views.about, name='about'),
    path('contacto/', views.contact, name='contact'),
    path('api/check-availability/', views.check_availability, name='check_availability'),
    path('api/contact/', views.contact_form, name='contact_form'),
    path('plan/<int:plan_id>/', views.plan_detalle, name='plan_detalle'),
    path('promocion/<int:promocion_id>/', views.promocion_detalle, name='promocion_detalle'),
    path("planes/", views.planes_list, name="planes_list"),
    path("promociones/", views.promociones_list, name="promociones_list"),
    path("seleccionar-plan/<int:plan_id>/", views.seleccionar_plan, name="seleccionar_plan"),
    path("seleccionar-promocion/<int:promo_id>/", views.seleccionar_promocion, name="seleccionar_promocion"),
]

