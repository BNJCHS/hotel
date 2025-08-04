from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ReservaTemp
from habitaciones.models import Habitacion

@login_required
def agregar_al_carrito(request, habitacion_id):
    habitacion = get_object_or_404(Habitacion, id=habitacion_id)
    ReservaTemp.objects.create(usuario=request.user, habitacion=habitacion)
    return redirect('ver_carrito')

@login_required
def ver_carrito(request):
    reservas = ReservaTemp.objects.filter(usuario=request.user)
    return render(request, 'reservas/carrito.html', {'reservas': reservas})

@login_required
def seleccionar_servicio(request, reserva_id):
    reserva = get_object_or_404(ReservaTemp, id=reserva_id, usuario=request.user)
    if request.method == 'POST':
        servicio = request.POST.get('servicio')
        reserva.servicio = servicio
        reserva.save()
        return redirect('ver_carrito')
    return render(request, 'reservas/seleccionar_servicio.html', {'reserva': reserva})
