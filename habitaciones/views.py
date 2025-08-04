
from django.shortcuts import render, get_object_or_404
from .models import Habitacion

def lista_habitaciones_publica(request):
    habitaciones = Habitacion.objects.all()
    return render(request, 'habitaciones/listar_habitaciones.html', {
        'habitaciones': habitaciones
    })

def detalle_habitacion_publica(request, id):
    habitacion = get_object_or_404(Habitacion, id=id)
    return render(request, 'habitaciones/detalle_habitacion.html', {
        'habitacion': habitacion
    })
