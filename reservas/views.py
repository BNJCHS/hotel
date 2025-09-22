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

from datetime import date, datetime
from decimal import Decimal
from .models import Huesped
from .forms import HuespedForm
from django.forms import modelformset_factory
from administracion.models import Plan, Promocion

@login_required
def detalle_reserva(request, reserva_id):
    """Vista para mostrar el detalle de una reserva específica y permitir agregar más habitaciones para las mismas fechas."""
    reservation = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)

    # Aliases para que el template actual funcione aunque el modelo use otros nombres
    reservation.room = reservation.habitacion
    reservation.checkin = reservation.check_in
    reservation.checkout = reservation.check_out
    reservation.guests = reservation.cantidad_huespedes
    reservation.total_price = reservation.monto
    reservation.status = 'confirmed' if reservation.confirmada else 'pending'

    # Calcular el número de noches
    try:
        if reservation.check_in and reservation.check_out:
            nights = (reservation.check_out - reservation.check_in).days or 1
        else:
            nights = 1
    except Exception:
        nights = 1
    reservation.nights = nights

    # Obtener información de huéspedes si existe
    guests_info = Huesped.objects.filter(reserva=reservation)
    if guests_info:
        reservation.guests_info = guests_info

    # Calcular habitaciones disponibles para agregar en las mismas fechas y capacidad
    available_rooms = []
    if reservation.checkin and reservation.checkout:
        candidate_qs = Habitacion.objects.filter(
            disponible=True,
            capacidad__gte=reservation.guests
        ).exclude(id=reservation.habitacion_id)

        for hab in candidate_qs:
            # verificar solapamiento con otras reservas de esa habitación
            overlapping = Reserva.objects.filter(
                habitacion=hab,
                check_in__lt=reservation.checkout,
                check_out__gt=reservation.checkin,
            ).exists()
            if not overlapping:
                available_rooms.append(hab)

    context = {
        'reservation': reservation,
        'available_rooms': available_rooms,
    }

    return render(request, 'detalle_reserva.html', context)


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
                    'error': 'La fecha de salida debe ser posterior a la de entrada',
                    'today': today,
                    'numero_huespedes': numero_huespedes
                })
        
        # Guardar en sesión
        request.session['numero_huespedes'] = numero_huespedes
        request.session['fecha_entrada'] = fecha_entrada
        request.session['fecha_salida'] = fecha_salida
        
        # Redirigir al nuevo paso: selección de tipos con stock
        return redirect('seleccionar_tipos')
    
    return render(request, 'reservas/seleccionar_huespedes.html', {
        'today': today,
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

            # Datos de pago SIMULADO (no se realiza ningún cobro real)
            sim_tx_id = None
            sim_tx_status = None
            if getattr(settings, "SIMULATE_PAYMENTS", False):
                sim_tx_id = f"SIM-{get_random_string(10)}"
                sim_tx_status = "aprobado"

            # Mostrar la página de "Reserva Enviada"
            return render(request, 'reservas/reserva_enviada.html', {
                'email': request.user.email,
                'simulate_payments': getattr(settings, "SIMULATE_PAYMENTS", False),
                'sim_tx_id': sim_tx_id,
                'sim_tx_status': sim_tx_status,
            })

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
        "simulate_payments": getattr(settings, "SIMULATE_PAYMENTS", False),
    })

@login_required
def confirmar_reserva_token(request, token):
    reserva = get_object_or_404(Reserva, token=token, usuario=request.user)
    reserva.confirmada = True
    reserva.save()
    return render(request, 'reservas/reserva_confirmada.html', {'reserva': reserva, 'simulate_payments': getattr(settings, "SIMULATE_PAYMENTS", False)})

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


# ===============================
# Agregar múltiples habitaciones a partir de una reserva existente
# ===============================
@login_required
def agregar_reservas_multiples(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    # Acepta tanto JSON como formulario
    habitaciones_ids = []
    try:
        if request.content_type == 'application/json':
            payload = json.loads(request.body or '{}')
            reserva_id = payload.get('reserva_id')
            habitaciones_ids = payload.get('habitaciones_ids', [])
            copiar_servicios = bool(payload.get('copiar_servicios', True))
        else:
            reserva_id = request.POST.get('reserva_id')
            habitaciones_ids = request.POST.getlist('habitaciones_ids')
            copiar_servicios = request.POST.get('copiar_servicios', '1') in ('1', 'true', 'on', 'True')
    except Exception:
        return JsonResponse({'success': False, 'error': 'Entrada inválida'}, status=400)

    base_reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)

    # Validaciones básicas
    if not habitaciones_ids:
        return JsonResponse({'success': False, 'error': 'Debe seleccionar al menos una habitación.'}, status=400)

    created_ids = []
    errors = []

    for hid in habitaciones_ids:
        try:
            hid_int = int(hid)
        except (TypeError, ValueError):
            errors.append(f"ID inválido: {hid}")
            continue

        if hid_int == base_reserva.habitacion_id:
            errors.append(f"La habitación {hid_int} ya está reservada en la reserva base.")
            continue

        hab = Habitacion.objects.filter(id=hid_int, disponible=True, capacidad__gte=base_reserva.cantidad_huespedes).first()
        if not hab:
            errors.append(f"Habitación no válida o sin capacidad: {hid_int}")
            continue

        # Chequear solapamiento con otras reservas
        overlap = Reserva.objects.filter(
            habitacion=hab,
            check_in__lt=base_reserva.check_out,
            check_out__gt=base_reserva.check_in,
        ).exists()
        if overlap:
            errors.append(f"La habitación {hab.numero} no está disponible en esas fechas.")
            continue

        nueva = Reserva.objects.create(
            usuario=request.user,
            habitacion=hab,
            check_in=base_reserva.check_in,
            check_out=base_reserva.check_out,
            metodo_pago=base_reserva.metodo_pago,
            plan=base_reserva.plan,
            promocion=base_reserva.promocion,
            cantidad_huespedes=base_reserva.cantidad_huespedes,
            confirmada=False,
        )

        # Copiar servicios
        if copiar_servicios:
            servicios_copiar = list(base_reserva.servicios.all())
            if servicios_copiar:
                nueva.servicios.add(*servicios_copiar)

        # Calcular monto
        nights = (base_reserva.check_out - base_reserva.check_in).days or 1
        precio_habitacion = hab.precio * nights
        precio_servicios = sum(s.precio for s in nueva.servicios.all())
        subtotal = precio_habitacion + precio_servicios
        if base_reserva.plan:
            subtotal += base_reserva.plan.precio
        if base_reserva.promocion:
            descuento = (subtotal * base_reserva.promocion.descuento) / 100
            subtotal -= descuento
        impuestos = subtotal * Decimal('0.18')
        total = subtotal + impuestos
        nueva.monto = total
        nueva.save()

        created_ids.append(nueva.id)

    # Si viene desde formulario HTML, redirigimos con mensajes
    if request.content_type != 'application/json':
        if created_ids:
            messages.success(request, f"Se crearon {len(created_ids)} reservas adicionales.")
        if errors:
            for e in errors:
                messages.warning(request, e)
        return redirect('mis_reservas')

    return JsonResponse({'success': True, 'creadas': created_ids, 'errores': errors, 'redirect_url': reverse('mis_reservas')}, status=200)


@login_required
def seleccionar_tipos(request):
    """
    Paso nuevo: permitir elegir múltiples tipos (Habitacion como TIPO) con cantidades,
    validando que la suma de capacidades cubra a los huéspedes y que el stock por fechas alcance.
    """
    # Datos requeridos desde la sesión
    numero_huespedes = request.session.get('numero_huespedes')
    fecha_entrada = request.session.get('fecha_entrada')
    fecha_salida = request.session.get('fecha_salida')

    if not (numero_huespedes and fecha_entrada and fecha_salida):
        messages.error(request, 'Primero selecciona las fechas y el número de huéspedes.')
        return redirect('seleccionar_huespedes')

    # Parsear fechas
    try:
        check_in = datetime.strptime(fecha_entrada, '%Y-%m-%d').date()
        check_out = datetime.strptime(fecha_salida, '%Y-%m-%d').date()
    except Exception:
        messages.error(request, 'Fechas inválidas.')
        return redirect('seleccionar_huespedes')

    # Obtener todos los tipos (Habitacion funciona como tipo con stock)
    tipos = Habitacion.objects.filter(disponible=True).order_by('precio')

    # Calcular disponibilidad (stock disponible) por tipo en el rango
    disponibles = {}
    for t in tipos:
        overlapping = Reserva.objects.filter(
            habitacion=t,
            check_in__lt=check_out,
            check_out__gt=check_in,
        ).count()
        disponibles[t.id] = max(0, t.stock - overlapping)

    # Anotar cada tipo con su stock disponible para el template
    for t in tipos:
        t.stock_disponible = disponibles.get(t.id, 0)
    if request.method == 'POST':
        # Recoger cantidades solicitadas
        seleccion = []  # lista de (habitacion_obj, cantidad)
        total_capacidad = 0
        for t in tipos:
            qty_str = request.POST.get(f'cantidad_{t.id}', '0').strip()
            try:
                qty = int(qty_str or 0)
            except ValueError:
                qty = 0
            if qty < 0:
                qty = 0
            if qty > 0:
                # Validar stock disponible
                if qty > disponibles.get(t.id, 0):
                    messages.error(request, f'No hay suficiente stock para {t.get_tipo_display()} (solicitado {qty}, disponible {disponibles.get(t.id, 0)}).')
                    return render(request, 'reservas/seleccionar_tipos.html', {
                        'tipos': tipos,
                        'disponibles': disponibles,
                        'numero_huespedes': numero_huespedes,
                        'fecha_entrada': fecha_entrada,
                        'fecha_salida': fecha_salida,
                    })
                seleccion.append((t, qty))
                total_capacidad += t.capacidad * qty

        if not seleccion:
            messages.error(request, 'Debes seleccionar al menos un tipo de habitación.')
            return render(request, 'reservas/seleccionar_tipos.html', {
                'tipos': tipos,
                'disponibles': disponibles,
                'numero_huespedes': numero_huespedes,
                'fecha_entrada': fecha_entrada,
                'fecha_salida': fecha_salida,
            })

        # Validar que la suma de capacidades cubra a los huéspedes
        if total_capacidad < int(numero_huespedes):
            messages.error(request, 'La combinación seleccionada no cubre la cantidad de huéspedes. Ajusta las cantidades.')
            return render(request, 'reservas/seleccionar_tipos.html', {
                'tipos': tipos,
                'disponibles': disponibles,
                'numero_huespedes': numero_huespedes,
                'fecha_entrada': fecha_entrada,
                'fecha_salida': fecha_salida,
            })

        # Crear reservas individuales por cada unidad solicitada
        noches = (check_out - check_in).days or 1
        created = []
        for t, qty in seleccion:
            for i in range(qty):
                r = Reserva.objects.create(
                    usuario=request.user,
                    habitacion=t,
                    check_in=check_in,
                    check_out=check_out,
                    metodo_pago='efectivo',
                    token=get_random_string(64),
                    cantidad_huespedes=min(t.capacidad, int(numero_huespedes)),
                    confirmada=False,
                )
                # Calcular monto base por habitación + impuestos (sin servicios ni plan/promoción aquí)
                precio_habitacion = t.precio * noches
                impuestos = precio_habitacion * Decimal('0.18')
                r.monto = precio_habitacion + impuestos
                r.save()
                created.append(r.id)

        messages.success(request, f'Se crearon {len(created)} reservas. Puedes revisarlas en Mis reservas.')
        return redirect('mis_reservas')

    return render(request, 'reservas/seleccionar_tipos.html', {
        'tipos': tipos,
        'disponibles': disponibles,
        'numero_huespedes': numero_huespedes,
        'fecha_entrada': fecha_entrada,
        'fecha_salida': fecha_salida,
    })