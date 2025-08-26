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
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from administracion.models import Servicio

@login_required
def seleccionar_fechas(request):
    if request.method == 'POST':
        fecha_entrada = request.POST.get('fecha_entrada')
        fecha_salida = request.POST.get('fecha_salida')
        numero_huespedes = request.POST.get('numero_huespedes')

        if not fecha_entrada or not fecha_salida or not numero_huespedes:
            return render(request, 'reservas/seleccionar_fechas.html', {'error': 'Todos los campos son obligatorios.'})

        request.session['fecha_entrada'] = fecha_entrada
        request.session['fecha_salida'] = fecha_salida
        request.session['numero_huespedes'] = numero_huespedes

        return redirect('lista_habitaciones')

    return render(request, 'reservas/seleccionar_fechas.html')
@login_required
@csrf_exempt
def agregar_servicio(request):
    if request.method == "POST":
        data = json.loads(request.body)
        servicio_id = data.get("servicio_id")

        try:
            servicio = Servicio.objects.get(id=servicio_id)
        except Servicio.DoesNotExist:
            return JsonResponse({"success": False, "error": "Servicio no encontrado"})

        carrito = request.session.get("servicios_seleccionados", [])
        if servicio.id not in carrito:
            carrito.append(servicio.id)
            request.session["servicios_seleccionados"] = carrito

        return JsonResponse({
            "success": True,
            "servicio": {
                "id": servicio.id,
                "nombre": servicio.nombre,
                "precio": float(servicio.precio)
            }
        })
    return JsonResponse({"success": False, "error": "Método no permitido"})


@login_required
@csrf_exempt
def quitar_servicio(request):
    if request.method == "POST":
        data = json.loads(request.body)
        servicio_id = data.get("servicio_id")

        carrito = request.session.get("servicios_seleccionados", [])
        if servicio_id in carrito:
            carrito.remove(servicio_id)
            request.session["servicios_seleccionados"] = carrito
            return JsonResponse({"success": True})

        return JsonResponse({"success": False, "error": "Servicio no estaba en el carrito"})

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
@login_required
def seleccionar_servicio(request):
    habitacion_id = request.session.get('habitacion_id')
    if not habitacion_id:
        return redirect('lista_habitaciones')

    habitacion = get_object_or_404(Habitacion, id=habitacion_id)
    servicios = Servicio.objects.all()

    if request.method == 'POST':
        servicios_seleccionados = request.POST.getlist('servicios')  # IDs de servicios
        metodo_pago = request.POST.get('metodo_pago', 'efectivo')

        # Guardamos en la sesión, todavía NO creamos la reserva
        request.session['servicios_seleccionados'] = servicios_seleccionados
        request.session['metodo_pago'] = metodo_pago

        return redirect('confirmar_reserva')

    return render(request, 'reservas/seleccionar_servicio.html', {
        'habitacion': habitacion,
        'servicios': servicios,
    })

def reserva_exitosa(request):
    return render(request, 'reservas/reserva_exitosa.html')

@login_required
def confirmar_reserva(request):
    habitacion_id = request.session.get('habitacion_id')
    servicios_ids = request.session.get('servicios_seleccionados', [])
    metodo_pago = request.session.get('metodo_pago', 'efectivo')

    if not habitacion_id:
        return redirect('lista_habitaciones')

    habitacion = get_object_or_404(Habitacion, id=habitacion_id)
    servicios = Servicio.objects.filter(id__in=servicios_ids)

    if request.method == 'POST':
        # Crear la reserva recién acá
        reserva = Reserva.objects.create(
            usuario=request.user,
            habitacion=habitacion,
            metodo_pago=metodo_pago
        )
        reserva.servicios.set(servicios)

        # limpiar sesión
        for key in ['habitacion_id', 'servicios_seleccionados', 'metodo_pago']:
            if key in request.session:
                del request.session[key]

        return redirect('detalle_reserva', reserva_id=reserva.id)

    return render(request, 'reservas/confirmar_reserva.html', {
        'habitacion': habitacion,
        'servicios': servicios,
        'metodo_pago': metodo_pago,
    })


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