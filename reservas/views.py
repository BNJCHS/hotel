from django.shortcuts import render, redirect, get_object_or_404
from .models import Reserva
from habitaciones.models import Habitacion, TipoHabitacion
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from usuarios.decorators import require_login_and_not_blocked
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
from django.db import models

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


@require_login_and_not_blocked
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
def seleccionar_servicio(request, reserva_id=None):
    # Si no se proporciona reserva_id, intentamos obtenerlo de la sesión
    if not reserva_id:
        reserva_id = request.session.get('reserva_id')
        if not reserva_id:
            return redirect('seleccionar_tipos')
    
    # Obtener la reserva
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)
    servicios = Servicio.objects.all()
    
    # Guardar el ID de la reserva en la sesión para pasos posteriores
    request.session['reserva_id'] = reserva.id

    if request.method == 'POST':
        servicios_seleccionados = request.POST.getlist('servicios')  # IDs de servicios
        metodo_pago = request.POST.get('metodo_pago', 'efectivo')

        # Actualizar método de pago si se proporciona
        if metodo_pago:
            reserva.metodo_pago = metodo_pago
        
        # Limpiar servicios existentes y agregar los nuevos
        reserva.servicios.clear()  # Eliminar todos los servicios existentes
        if servicios_seleccionados:
            servicios_obj = Servicio.objects.filter(id__in=servicios_seleccionados)
            reserva.servicios.add(*servicios_obj)
        
        # Calcular precio
        noches = (reserva.check_out - reserva.check_in).days or 1
        precio_habitacion = reserva.tipo_habitacion.precio * reserva.cantidad_habitaciones * noches
        precio_servicios = sum(servicio.precio for servicio in reserva.servicios.all())
        subtotal = precio_habitacion + precio_servicios
        impuestos = subtotal * Decimal("0.18")
        precio_total = subtotal + impuestos
        
        reserva.monto = precio_total
        reserva.save()

        # Redirigir a la página de confirmación con el ID de la reserva
        return redirect('confirmar_reserva', reserva_id=reserva.id)

    # Obtener los servicios ya seleccionados para esta reserva
    servicios_seleccionados = list(reserva.servicios.all().values('id', 'nombre', 'precio'))
    
    return render(request, 'reservas/seleccionar_servicio.html', {
        'reserva': reserva,
        'tipo_habitacion': reserva.tipo_habitacion,
        'servicios': servicios,
        'servicios_seleccionados_json': json.dumps(servicios_seleccionados),
    })

def reserva_exitosa(request):
    return render(request, 'reservas/reserva_exitosa.html')

from decimal import Decimal

from datetime import datetime


@require_login_and_not_blocked
def confirmar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)

    noches = 1
    if reserva.check_in and reserva.check_out:
        noches = (reserva.check_out - reserva.check_in).days or 1

    precio_habitacion = reserva.tipo_habitacion.precio * reserva.cantidad_habitaciones * noches
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
            reserva.estado = 'pendiente'  # aún pendiente de confirmar por email
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
            sim_payment_provider = None
            
            if getattr(settings, "SIMULATE_PAYMENTS", False):
                # Generar ID de transacción simulada
                sim_tx_id = f"SIM-{get_random_string(10)}"
                sim_tx_status = "aprobado"
                
                # Personalizar información según el método de pago
                if metodo_pago == 'mercadopago':
                    sim_payment_provider = "MercadoPago"
                    sim_tx_id = f"MP-{get_random_string(8).upper()}"
                elif metodo_pago == 'paypal':
                    sim_payment_provider = "PayPal"
                    sim_tx_id = f"PP-{get_random_string(12).upper()}"
                elif metodo_pago == 'crypto':
                    sim_payment_provider = "Crypto"
                    sim_tx_id = f"0x{get_random_string(40, allowed_chars='0123456789abcdef')}"
                elif metodo_pago == 'transferencia':
                    sim_payment_provider = "Banco"
                    sim_tx_id = f"TR-{get_random_string(10).upper()}"
                else:
                    sim_payment_provider = "Tarjeta"

            # Mostrar la página de "Reserva Enviada"
            return render(request, 'reservas/reserva_enviada.html', {
                'email': request.user.email,
                'simulate_payments': getattr(settings, "SIMULATE_PAYMENTS", False),
                'sim_tx_id': sim_tx_id,
                'sim_tx_status': sim_tx_status,
                'sim_payment_provider': sim_payment_provider,
                'metodo_pago': metodo_pago,
            })

    return render(request, "reservas/confirmar_reserva.html", {
        "reserva": reserva,
        "tipo_habitacion": reserva.tipo_habitacion,
        "cantidad_habitaciones": reserva.cantidad_habitaciones,
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
    reserva.estado = 'confirmada'
    reserva.save()
    
    # Procesar tipos adicionales si existen
    tipos_adicionales = request.session.get('tipos_adicionales', [])
    if tipos_adicionales:
        for tipo_id, qty in tipos_adicionales:
            try:
                tipo = TipoHabitacion.objects.get(id=tipo_id)
                # Crear reserva adicional
                nueva_reserva = Reserva.objects.create(
                    usuario=request.user,
                    tipo_habitacion=tipo,
                    cantidad_habitaciones=qty,
                    check_in=reserva.check_in,
                    check_out=reserva.check_out,
                    cantidad_huespedes=reserva.cantidad_huespedes,
                    estado='confirmada',
                    metodo_pago=reserva.metodo_pago,
                    token=get_random_string(64),
                )
                # Calcular monto
                noches = (reserva.check_out - reserva.check_in).days or 1
                precio_total = tipo.precio * qty * noches
                impuestos = precio_total * Decimal('0.18')
                nueva_reserva.monto = precio_total + impuestos
                nueva_reserva.save()
                
                # Reservar stock
                tipo.reservar_stock(qty)
            except TipoHabitacion.DoesNotExist:
                pass
        
        # Limpiar la sesión
        del request.session['tipos_adicionales']
    
    return render(request, 'reservas/reserva_confirmada.html', {'reserva': reserva, 'simulate_payments': getattr(settings, "SIMULATE_PAYMENTS", False)})

@login_required
def mis_reservas(request):
    reservas = Reserva.objects.filter(usuario=request.user).select_related('tipo_habitacion').order_by('-fecha_reserva')
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
@require_login_and_not_blocked
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
    Vista para seleccionar tipos de habitaciones con stock disponible.
    Permite elegir múltiples tipos con cantidades, validando capacidad y stock.
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

    # Obtener todos los tipos de habitaciones activos
    tipos = TipoHabitacion.objects.filter(activo=True).order_by('precio')

    # Calcular disponibilidad por tipo en el rango de fechas
    disponibles = {}
    for tipo in tipos:
        # Contar reservas que se solapan con las fechas solicitadas
        reservas_solapadas = Reserva.objects.filter(
            tipo_habitacion=tipo,
            check_in__lt=check_out,
            check_out__gt=check_in,
            estado__in=['confirmada', 'activa']
        ).aggregate(total=models.Sum('cantidad_habitaciones'))['total'] or 0
        
        disponibles[tipo.id] = max(0, tipo.stock_disponible - reservas_solapadas)

    # Anotar cada tipo con su stock disponible para el template
    for tipo in tipos:
        tipo.stock_disponible_fechas = disponibles.get(tipo.id, 0)
    if request.method == 'POST':
        # Recoger cantidades solicitadas
        seleccion = []  # lista de (tipo_habitacion_obj, cantidad)
        total_capacidad = 0
        for tipo in tipos:
            qty_str = request.POST.get(f'cantidad_{tipo.id}', '0').strip()
            try:
                qty = int(qty_str or 0)
            except ValueError:
                qty = 0
            if qty < 0:
                qty = 0
            if qty > 0:
                # Validar stock disponible
                if qty > disponibles.get(tipo.id, 0):
                    messages.error(request, f'No hay suficiente stock para {tipo.nombre} (solicitado {qty}, disponible {disponibles.get(tipo.id, 0)}).')
                    return render(request, 'reservas/seleccionar_tipos.html', {
                        'tipos': tipos,
                        'disponibles': disponibles,
                        'numero_huespedes': numero_huespedes,
                        'fecha_entrada': fecha_entrada,
                        'fecha_salida': fecha_salida,
                    })
                seleccion.append((tipo, qty))
                total_capacidad += tipo.capacidad * qty

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

        # Crear reservas con el nuevo modelo
        noches = (check_out - check_in).days or 1
        created = []
        
        # Crear una sola reserva para el primer tipo seleccionado
        # (para mantener el flujo de selección de servicios y confirmación)
        tipo, qty = seleccion[0]
        reserva = Reserva.objects.create(
            usuario=request.user,
            tipo_habitacion=tipo,
            cantidad_habitaciones=qty,
            check_in=check_in,
            check_out=check_out,
            cantidad_huespedes=int(numero_huespedes),
            estado='pendiente',
            token=get_random_string(64),
        )
        
        # Calcular monto inicial (se actualizará en pasos posteriores)
        precio_total = tipo.precio * qty * noches
        impuestos = precio_total * Decimal('0.18')
        reserva.monto = precio_total + impuestos
        reserva.save()
        
        # Reservar stock
        tipo.reservar_stock(qty)
        
        # Guardar el ID de la reserva en la sesión para el siguiente paso
        request.session['reserva_id'] = reserva.id
        
        # Si hay más tipos seleccionados, los guardamos para procesarlos después
        if len(seleccion) > 1:
            request.session['tipos_adicionales'] = [(t.id, q) for t, q in seleccion[1:]]
        
        # Redirigir a la selección de servicios
        return redirect('seleccionar_servicio_con_id', reserva_id=reserva.id)

    return render(request, 'reservas/seleccionar_tipos.html', {
        'tipos': tipos,
        'disponibles': disponibles,
        'numero_huespedes': numero_huespedes,
        'fecha_entrada': fecha_entrada,
        'fecha_salida': fecha_salida,
    })