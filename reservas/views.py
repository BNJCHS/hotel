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

@login_required
def seleccionar_fechas(request):
    today = date.today().isoformat()
    HuespedFormSet = modelformset_factory(Huesped, form=HuespedForm, extra=0, can_delete=False)

    if request.method == 'POST':
        fecha_entrada = request.POST.get('fecha_entrada')
        fecha_salida = request.POST.get('fecha_salida')
        numero_huespedes = int(request.POST.get('numero_huespedes', 0))

        if not fecha_entrada or not fecha_salida or numero_huespedes < 1:
            return render(request, 'reservas/seleccionar_fechas.html', {'error': 'Todos los campos son obligatorios.', 'today': today})

        # Guardar fechas y cantidad en sesión
        request.session['fecha_entrada'] = fecha_entrada
        request.session['fecha_salida'] = fecha_salida
        request.session['numero_huespedes'] = numero_huespedes

        # Crear formset con el número de huéspedes
        if 'huespedes_submitted' in request.POST:
            formset = HuespedFormSet(request.POST, queryset=Huesped.objects.none())
            if formset.is_valid():
                # Guardar huéspedes en sesión o en DB
                huespedes_data = formset.cleaned_data
                request.session['huespedes'] = huespedes_data
                return redirect('lista_habitaciones')
        else:
            HuespedFormSetExtra = modelformset_factory(Huesped, form=HuespedForm, extra=numero_huespedes, can_delete=False)
            formset = HuespedFormSetExtra(queryset=Huesped.objects.none())

        return render(request, 'reservas/seleccionar_fechas.html', {
            'formset': formset,
            'fecha_entrada': fecha_entrada,
            'fecha_salida': fecha_salida,
            'numero_huespedes': numero_huespedes,
            'today': today,
        })

    return render(request, 'reservas/seleccionar_fechas.html', {'today': today})
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

from decimal import Decimal

@login_required
def confirmar_reserva(request):
    habitacion_id = request.session.get('habitacion_id')
    servicios_ids = request.session.get('servicios_seleccionados', [])
    plan_id = request.session.get('plan_id')
    promocion_id = request.session.get('promocion_id')
    fecha_entrada = request.session.get('fecha_entrada')
    fecha_salida = request.session.get('fecha_salida')
    numero_huespedes = request.session.get('numero_huespedes', 1)

    if not habitacion_id or not fecha_entrada or not fecha_salida:
        return redirect('lista_habitaciones')

    habitacion = get_object_or_404(Habitacion, id=habitacion_id)
    servicios = Servicio.objects.filter(id__in=servicios_ids)

    plan = None
    promocion = None
    precio_total = Decimal('0')

    # Si eligió un plan
    if plan_id:
        plan = get_object_or_404(Plan, id=plan_id)
        precio_total = Decimal(plan.precio)

    # Si eligió una promoción
    elif promocion_id:
        promocion = get_object_or_404(Promocion, id=promocion_id)
        precio_habitacion = Decimal(habitacion.precio)
        precio_servicios = sum(Decimal(servicio.precio) for servicio in servicios)
        subtotal = precio_habitacion + precio_servicios
        descuento = (promocion.descuento / Decimal('100')) * subtotal
        precio_total = subtotal - descuento

    # Si no hay plan ni promoción → lógica normal
    else:
        precio_habitacion = Decimal(habitacion.precio)
        precio_servicios = sum(Decimal(servicio.precio) for servicio in servicios)
        impuestos = Decimal('0.18') * (precio_habitacion + precio_servicios)
        precio_total = precio_habitacion + precio_servicios + impuestos

    if request.method == 'POST':
        reserva = Reserva.objects.create(
            usuario=request.user,
            habitacion=habitacion,
            plan=plan,
            promocion=promocion,
            check_in=fecha_entrada,
            check_out=fecha_salida,
            cantidad_huespedes=numero_huespedes,
            monto=precio_total,
            metodo_pago=request.POST.get('metodo_pago', 'efectivo'),
            confirmada=True
        )
        reserva.servicios.set(servicios)

        # Limpiar sesión
        for key in ['habitacion_id', 'servicios_seleccionados', 'plan_id', 'promocion_id', 'fecha_entrada', 'fecha_salida', 'numero_huespedes']:
            request.session.pop(key, None)

        # Enviar email confirmación
        token_url = request.build_absolute_uri(
            reverse('confirmar_reserva_token', args=[reserva.token])
        )
        send_mail(
            subject='Confirma tu reserva',
            message=f'Hola {request.user.first_name}, confirma tu reserva haciendo clic en este enlace:\n{token_url}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[request.user.email],
        )

        return render(request, 'reservas/reserva_enviada.html', {'email': request.user.email})

    return render(request, 'reservas/confirmar_reserva.html', {
        'habitacion': habitacion,
        'servicios': servicios,
        'plan': plan,
        'promocion': promocion,
        'precio_total': precio_total,
        'fecha_entrada': fecha_entrada,
        'fecha_salida': fecha_salida,
        'numero_huespedes': numero_huespedes,
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