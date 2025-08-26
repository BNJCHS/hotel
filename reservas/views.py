from django.shortcuts import render, redirect, get_object_or_404
from .models import Reserva
from .forms import SeleccionarServicioForm
from habitaciones.models import Habitacion
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from administracion.models import Servicio
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@login_required
@csrf_exempt  # o usar csrf token desde JS
def agregar_servicio(request):
    if request.method == "POST":
        data = json.loads(request.body)
        servicio_id = data.get("servicio_id")
        habitacion_id = request.session.get("habitacion_id")

        if not habitacion_id:
            return JsonResponse({"success": False, "error": "No hay habitación seleccionada"})

        habitacion = Habitacion.objects.get(id=habitacion_id)
        servicio = Servicio.objects.get(id=servicio_id)

        # Guardar reserva en DB
        reserva = Reserva.objects.create(
            usuario=request.user,
            habitacion=habitacion,
            servicio=servicio
        )

        return JsonResponse({
            "success": True,
            "servicio": {
                "id": servicio.id,
                "nombre": servicio.nombre,
                "precio": servicio.precio
            }
        })

    return JsonResponse({"success": False, "error": "Método no permitido"})


@login_required
def agregar_al_carrito(request, habitacion_id):
    habitacion = get_object_or_404(Habitacion, id=habitacion_id)
    request.session['habitacion_id'] = habitacion.id
    return redirect('seleccionar_servicio')

@login_required
def seleccionar_servicio(request):
    habitacion_id = request.session.get('habitacion_id')
    if not habitacion_id:
        return redirect('lista_habitaciones')

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

    # 🚀 acá cargamos los servicios de la BD
    servicios = Servicio.objects.all()

    return render(request, 'reservas/seleccionar_servicio.html', {
        'form': form,
        'habitacion': habitacion,
        'servicios': servicios  # <<--- ahora el template recibe servicios
    })



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