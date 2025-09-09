from django.shortcuts import render, redirect, get_object_or_404
from .models import Reserva
from habitaciones.models import Habitacion
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from administracion.models import Servicio
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings

from datetime import date
from decimal import Decimal
from .models import Huesped
from .forms import HuespedForm
from django.forms import modelformset_factory
from administracion.models import Plan, Promocion


@login_required
def reservar_habitacion(request, habitacion_id):
    habitacion = get_object_or_404(Habitacion, id=habitacion_id)
    request.session['habitacion_id'] = habitacion.id  # Guardamos la habitación en sesión
    return redirect('seleccionar_fechas')

@login_required
def seleccionar_fechas(request):
    today = date.today().isoformat()
    HuespedFormSet = modelformset_factory(Huesped, form=HuespedForm, extra=0, can_delete=False)

    habitacion_id = request.session.get('habitacion_id')
    if not habitacion_id:
        return redirect('list_habitaciones')  # Si no hay habitación seleccionada, volvemos

    habitacion = Habitacion.objects.get(id=habitacion_id)

    if request.method == 'POST':
        fecha_entrada = request.POST.get('fecha_entrada')
        fecha_salida = request.POST.get('fecha_salida')
        numero_huespedes = int(request.POST.get('numero_huespedes', 0))

        if not fecha_entrada or not fecha_salida or numero_huespedes < 1:
            return render(request, 'reservas/seleccionar_fechas.html', {
                'error': 'Todos los campos son obligatorios.', 
                'today': today,
                'habitacion': habitacion
            })

        request.session['fecha_entrada'] = fecha_entrada
        request.session['fecha_salida'] = fecha_salida
        request.session['numero_huespedes'] = numero_huespedes

        # Formset de huéspedes
        if 'huespedes_submitted' in request.POST:
            formset = HuespedFormSet(request.POST, queryset=Huesped.objects.none())
            if formset.is_valid():
                huespedes_data = formset.cleaned_data
                request.session['huespedes'] = huespedes_data
                return redirect('seleccionar_servicio')
        else:
            HuespedFormSetExtra = modelformset_factory(Huesped, form=HuespedForm, extra=numero_huespedes, can_delete=False)
            formset = HuespedFormSetExtra(queryset=Huesped.objects.none())

        return render(request, 'reservas/seleccionar_fechas.html', {
            'formset': formset,
            'fecha_entrada': fecha_entrada,
            'fecha_salida': fecha_salida,
            'numero_huespedes': numero_huespedes,
            'today': today,
            'habitacion': habitacion
        })

    return render(request, 'reservas/seleccionar_fechas.html', {
        'today': today,
        'habitacion': habitacion
    })
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

from decimal import Decimal

from datetime import datetime


@login_required
def confirmar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)

    noches = 1
    if reserva.check_in and reserva.check_out:
        noches = (reserva.check_out - reserva.check_in).days or 1

    precio_habitacion = reserva.habitacion.precio * noches
    precio_servicios = sum(servicio.precio for servicio in reserva.servicios.all())
    subtotal = precio_habitacion + precio_servicios

    if reserva.plan:
        subtotal += reserva.plan.precio

    descuento = 0
    if reserva.promocion:
        descuento = (subtotal * reserva.promocion.descuento) / 100
        subtotal -= descuento

    impuestos = subtotal * Decimal("0.18")
    precio_total = subtotal + impuestos

    if request.method == "POST":
        metodo_pago = request.POST.get("metodo_pago")
        if metodo_pago:
            reserva.metodo_pago = metodo_pago
            reserva.monto = precio_total
            reserva.confirmada = False  # aún pendiente de confirmar
            reserva.save()

            # Enviar correo de confirmación
            confirm_url = request.build_absolute_uri(
                reverse("confirmar_reserva_token", args=[reserva.token])
            )
            send_mail(
                "Confirma tu reserva",
                f"Hola {request.user.username}, por favor confirma tu reserva haciendo clic en el siguiente enlace:\n{confirm_url}",
                settings.DEFAULT_FROM_EMAIL,
                [request.user.email],
                fail_silently=False,
            )

            # Mostrar la página de "Reserva Enviada"
            return render(request, 'reservas/reserva_enviada.html', {'email': request.user.email})

    return render(request, "reservas/confirmar_reserva.html", {
        "reserva": reserva,
        "habitacion": reserva.habitacion,
        "servicios_seleccionados": reserva.servicios.all(),
        "precio_habitacion": precio_habitacion,
        "precio_servicios": precio_servicios,
        "descuento": descuento,
        "impuestos": impuestos,
        "precio_total": precio_total,
        "noches": noches,
    })

@login_required
def confirmar_reserva_token(request, token):
    reserva = get_object_or_404(Reserva, token=token, usuario=request.user)
    reserva.confirmada = True
    reserva.save()
    return render(request, 'reservas/reserva_confirmada.html', {'reserva': reserva})

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