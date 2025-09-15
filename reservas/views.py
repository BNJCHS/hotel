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
def seleccionar_huespedes(request):
    today = datetime.now().date().strftime('%Y-%m-%d')
    
    if request.method == 'POST':
        numero_huespedes = int(request.POST.get('numero_huespedes', 1))
        fecha_entrada = request.POST.get('fecha_entrada')
        fecha_salida = request.POST.get('fecha_salida')
        
        # Validar fechas
        if fecha_entrada and fecha_salida:
            fecha_entrada_obj = datetime.strptime(fecha_entrada, '%Y-%m-%d').date()
            fecha_salida_obj = datetime.strptime(fecha_salida, '%Y-%m-%d').date()
            
            if fecha_entrada_obj < datetime.now().date():
                return render(request, 'reservas/seleccionar_huespedes.html', {
                    'error': 'La fecha de entrada no puede ser anterior a hoy',
                    'today': today,
                    'numero_huespedes': numero_huespedes
                })
            
            if fecha_salida_obj <= fecha_entrada_obj:
                return render(request, 'reservas/seleccionar_huespedes.html', {
                    'error': 'La fecha de salida debe ser posterior a la fecha de entrada',
                    'today': today,
                    'numero_huespedes': numero_huespedes,
                    'fecha_entrada': fecha_entrada
                })
        
        # Guardar en sesión
        request.session['numero_huespedes'] = numero_huespedes
        request.session['fecha_entrada'] = fecha_entrada
        request.session['fecha_salida'] = fecha_salida
        
        # Redirigir a lista de habitaciones
        return redirect('habitaciones_lista')
    
    # Obtener valores de sesión si existen
    numero_huespedes = request.session.get('numero_huespedes', 1)
    fecha_entrada = request.session.get('fecha_entrada', '')
    fecha_salida = request.session.get('fecha_salida', '')
    
    return render(request, 'reservas/seleccionar_huespedes.html', {
        'today': today,
        'numero_huespedes': numero_huespedes,
        'fecha_entrada': fecha_entrada,
        'fecha_salida': fecha_salida
    })

@login_required
def reservar_habitacion(request, habitacion_id):
    habitacion = get_object_or_404(Habitacion, id=habitacion_id)
    
    # Verificar si hay número de huéspedes en la sesión
    numero_huespedes = request.session.get('numero_huespedes')
    if not numero_huespedes:
        return redirect('seleccionar_huespedes')
    
    # Verificar si la habitación tiene capacidad suficiente
    if habitacion.capacidad < numero_huespedes:
        messages.error(request, f'Esta habitación solo tiene capacidad para {habitacion.capacidad} personas.')
        return redirect('habitaciones_lista')
    
    request.session['habitacion_id'] = habitacion.id  # Guardamos la habitación en sesión
    return redirect('seleccionar_fechas')

@login_required
def seleccionar_fechas(request):
    today = date.today().isoformat()
    
    # Verificar si hay número de huéspedes en la sesión
    numero_huespedes = request.session.get('numero_huespedes')
    fecha_entrada = request.session.get('fecha_entrada')
    fecha_salida = request.session.get('fecha_salida')
    
    if not numero_huespedes or not fecha_entrada or not fecha_salida:
        return redirect('seleccionar_huespedes')  # Si no hay datos de huéspedes, volvemos
    
    habitacion_id = request.session.get('habitacion_id')
    if not habitacion_id:
        return redirect('habitaciones_lista')  # Si no hay habitación seleccionada, volvemos

    habitacion = Habitacion.objects.get(id=habitacion_id)
    
    # Verificar si la habitación tiene capacidad suficiente
    if habitacion.capacidad < numero_huespedes:
        messages.error(request, f'Esta habitación solo tiene capacidad para {habitacion.capacidad} personas.')
        return redirect('habitaciones_lista')

    if request.method == 'POST':
        # Formset de huéspedes
        HuespedFormSetExtra = modelformset_factory(Huesped, form=HuespedForm, extra=numero_huespedes, can_delete=False)
        
        if 'huespedes_submitted' in request.POST:
            formset = HuespedFormSetExtra(request.POST, queryset=Huesped.objects.none())
            if formset.is_valid():
                huespedes_data = formset.cleaned_data
                request.session['huespedes'] = huespedes_data
                return redirect('seleccionar_servicio')
        else:
            formset = HuespedFormSetExtra(queryset=Huesped.objects.none())

        return render(request, 'reservas/seleccionar_fechas.html', {
            'formset': formset,
            'fecha_entrada': fecha_entrada,
            'fecha_salida': fecha_salida,
            'numero_huespedes': numero_huespedes,
            'today': today,
            'habitacion': habitacion
        })

    # Crear formset para los huéspedes
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
        return redirect('habitaciones_lista')

    habitacion = get_object_or_404(Habitacion, id=habitacion_id)
    servicios = Servicio.objects.all()
    
    # Obtener datos de la sesión
    fecha_entrada = request.session.get('fecha_entrada')
    fecha_salida = request.session.get('fecha_salida')
    numero_huespedes = request.session.get('numero_huespedes')
    
    if not fecha_entrada or not fecha_salida or not numero_huespedes:
        return redirect('seleccionar_huespedes')

    if request.method == 'POST':
        servicios_seleccionados = request.POST.getlist('servicios')  # IDs de servicios
        metodo_pago = request.POST.get('metodo_pago', 'efectivo')

        # Crear la reserva
        reserva = Reserva.objects.create(
            habitacion=habitacion,
            usuario=request.user,
            check_in=fecha_entrada,
            check_out=fecha_salida,
            metodo_pago=metodo_pago,
            token=get_random_string(64),
            cantidad_huespedes=numero_huespedes
        )
        
        # Agregar servicios a la reserva
        if servicios_seleccionados:
            servicios_obj = Servicio.objects.filter(id__in=servicios_seleccionados)
            reserva.servicios.add(*servicios_obj)
        
        # Calcular precio
        noches = (datetime.strptime(fecha_salida, '%Y-%m-%d').date() - 
                 datetime.strptime(fecha_entrada, '%Y-%m-%d').date()).days or 1
        precio_habitacion = habitacion.precio * noches
        precio_servicios = sum(servicio.precio for servicio in reserva.servicios.all())
        subtotal = precio_habitacion + precio_servicios
        impuestos = subtotal * Decimal("0.18")
        precio_total = subtotal + impuestos
        
        reserva.monto = precio_total
        reserva.save()

        # Redirigir a la página de confirmación con el ID de la reserva
        return redirect('confirmar_reserva', reserva_id=reserva.id)

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