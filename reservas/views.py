from django.shortcuts import render, redirect, get_object_or_404
from .models import Reserva
from .forms import SeleccionarServicioForm
from habitaciones.models import Habitacion
from django.contrib.auth.decorators import login_required
from django.contrib import messages
@login_required
def agregar_al_carrito(request, habitacion_id):
    habitacion = get_object_or_404(Habitacion, id=habitacion_id)
    request.session['habitacion_id'] = habitacion.id
    return redirect('seleccionar_servicio')


@login_required
def seleccionar_servicio(request):
    habitacion_id = request.session.get('habitacion_id')
    if not habitacion_id:
        return redirect('lista_habitaciones')  # O donde muestres las habitaciones

    habitacion = get_object_or_404(Habitacion, id=habitacion_id)

    if request.method == 'POST':
        form = SeleccionarServicioForm(request.POST)
        if form.is_valid():
            reserva = form.save(commit=False)
            reserva.usuario = request.user
            reserva.habitacion = habitacion
            reserva.save()
            del request.session['habitacion_id']  # Limpiar carrito
            return redirect('reserva_exitosa')
    else:
        form = SeleccionarServicioForm()

    return render(request, 'reservas/seleccionar_servicio.html', {'form': form, 'habitacion': habitacion})


def reserva_exitosa(request):
    return render(request, 'reservas/reserva_exitosa.html')

@login_required
def mis_reservas(request):
    reservas = Reserva.objects.filter(usuario=request.user).select_related('habitacion')
    return render(request, 'reservas/mis_reservas.html', {'reservas': reservas})



@login_required
def cancelar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)
    reserva.delete()
    messages.success(request, "La reserva fue cancelada exitosamente.")
    return redirect('mis_reservas')