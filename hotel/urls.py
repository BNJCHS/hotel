from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('sobre-nosotros/', views.about, name='about'),
    path('contacto/', views.contact, name='contact'),
    path('api/check-availability/', views.check_availability, name='check_availability'),
    path('api/contact/', views.contact_form, name='contact_form'),
]

