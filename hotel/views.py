from django.shortcuts import render,redirect,get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, get_object_or_404
from administracion.models import Plan, Promocion
from django.contrib.auth.decorators import login_required
from reservas.models import Reserva
from habitaciones.models import Habitacion
from django.contrib import messages
from usuarios.decorators import require_login_and_not_blocked
import json
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from administracion.models import Servicio

def lista_habitaciones(request):
    numero_huespedes = request.session.get('numero_huespedes', None)
    fecha_entrada = request.session.get('fecha_entrada', None)
    fecha_salida = request.session.get('fecha_salida', None)
    if not numero_huespedes:
        return redirect('reservas:seleccionar_huespedes')
    habitaciones = Habitacion.objects.filter(disponible=True, capacidad__gte=numero_huespedes)
    context = {
        'habitaciones': habitaciones,
        'numero_huespedes': numero_huespedes,
        'fecha_entrada': fecha_entrada,
        'fecha_salida': fecha_salida
    }
    return render(request, 'lista_habitaciones.html', context)

def lista_habitaciones_explorar(request):
    habitaciones = Habitacion.objects.select_related('tipo_habitacion').all()

    tipo = request.GET.get('tipo', '').strip()
    capacidad_min = request.GET.get('capacidad_min', '').strip()
    precio_min = request.GET.get('precio_min', '').strip()
    precio_max = request.GET.get('precio_max', '').strip()
    solo_disponibles = request.GET.get('solo_disponibles', '').strip()

    from habitaciones.models import TipoHabitacion
    from decimal import Decimal

    if tipo:
        habitaciones = habitaciones.filter(tipo_habitacion__nombre__icontains=tipo)
    if capacidad_min:
        try:
            habitaciones = habitaciones.filter(tipo_habitacion__capacidad__gte=int(capacidad_min))
        except ValueError:
            pass
    if precio_min:
        try:
            habitaciones = habitaciones.filter(tipo_habitacion__precio__gte=Decimal(precio_min))
        except Exception:
            pass
    if precio_max:
        try:
            habitaciones = habitaciones.filter(tipo_habitacion__precio__lte=Decimal(precio_max))
        except Exception:
            pass
    if solo_disponibles in ('1', 'true', 'True', 'on'):
        habitaciones = habitaciones.filter(disponible=True, en_mantenimiento=False, tipo_habitacion__activo=True)

    tipos = list(TipoHabitacion.objects.filter(activo=True).values_list('nombre', flat=True))

    return render(request, 'habitaciones/listar_habitaciones.html', {
        'habitaciones': habitaciones,
        'tipos': tipos,
        'filtros': {
            'tipo': tipo,
            'capacidad_min': capacidad_min,
            'precio_min': precio_min,
            'precio_max': precio_max,
            'solo_disponibles': solo_disponibles,
        }
    })
def habitacion_detalle(request, id):
    habitacion = get_object_or_404(Habitacion, id=id)
    
    # Obtener número de huéspedes de la sesión
    numero_huespedes = request.session.get('numero_huespedes', None)
    
    # Verificar si la habitación tiene capacidad suficiente
    if numero_huespedes and habitacion.capacidad < numero_huespedes:
        messages.error(request, f'Esta habitación solo tiene capacidad para {habitacion.capacidad} personas.')
        return redirect('lista_habitaciones')
    
    context = {
        'habitacion': habitacion
    }
    return render(request, 'habitacion_detalle.html', context)

# vistas.py
def seleccionar_habitacion(request, habitacion_id):
    request.session['habitacion_id'] = habitacion_id
    return redirect('reservas:seleccionar_fechas')


def index(request):
    # Limpiar la sesión para iniciar un nuevo proceso de reserva
    if 'numero_huespedes' in request.session:
        del request.session['numero_huespedes']
    if 'fecha_entrada' in request.session:
        del request.session['fecha_entrada']
    if 'fecha_salida' in request.session:
        del request.session['fecha_salida']
    if 'habitacion_id' in request.session:
        del request.session['habitacion_id']
    
    # Traemos los primeros 3 planes y promociones
    planes = Plan.objects.all()[:3]
    promociones = Promocion.objects.all()[:3]

    # Traemos todas las habitaciones y servicios (o los primeros 6 si querés limitar)
    habitaciones = Habitacion.objects.all()[:6]
    servicios = Servicio.objects.all()  # Podés limitar con [:6] si querés

    context = {
        'planes': planes,
        'promociones': promociones,
        'habitaciones': habitaciones,
        'servicios': servicios
    }

    return render(request, 'index.html', context)
def about(request):
    """
    Vista de la página Sobre Nosotros
    """
    context = {
        'page_title': 'Sobre Nosotros - Hotel Elegante',
        'meta_description': 'Conoce la historia, valores y equipo detrás de Hotel Elegante. Más de 35 años de experiencia en hospitalidad de lujo.',
    }
    return render(request, 'about.html', context)

def contact(request):
    """
    Vista de la página de Contacto
    """
    if request.method == 'POST':
        # Procesar formulario de contacto
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        
        # Validaciones básicas
        if not first_name or not last_name or not email or not subject or not message:
            context = {
                'error': 'Por favor, completa todos los campos requeridos',
                'form_data': request.POST
            }
            return render(request, 'contacto.html', context)
        
        # Aquí normalmente guardarías en la base de datos y/o enviarías un email
        # Por ahora solo simulamos el procesamiento
        
        context = {
            'success': 'Mensaje enviado correctamente. Te contactaremos pronto.',
            'page_title': 'Contacto - Hotel Elegante',
            'meta_description': 'Ponte en contacto con Hotel Elegante. Estamos aquí para ayudarte con reservas, consultas y cualquier información que necesites.',
        }
        return render(request, 'contacto.html', context)
    
    context = {
        'page_title': 'Contacto - Hotel Elegante',
        'meta_description': 'Ponte en contacto con Hotel Elegante. Estamos aquí para ayudarte con reservas, consultas y cualquier información que necesites.',
    }
    return render(request, 'contacto.html', context)

@require_http_methods(["POST"])
def check_availability(request):
    """
    API endpoint para verificar disponibilidad de habitaciones
    """
    try:
        data = json.loads(request.body)
        checkin = data.get('checkin')
        checkout = data.get('checkout')
        guests = data.get('guests', 1)
        
        # Validar fechas
        checkin_date = datetime.strptime(checkin, '%Y-%m-%d').date()
        checkout_date = datetime.strptime(checkout, '%Y-%m-%d').date()
        today = datetime.now().date()
        
        if checkin_date < today:
            return JsonResponse({
                'success': False,
                'message': 'La fecha de entrada no puede ser anterior a hoy'
            }, status=400)
        
        if checkout_date <= checkin_date:
            return JsonResponse({
                'success': False,
                'message': 'La fecha de salida debe ser posterior a la fecha de entrada'
            }, status=400)
        
        # Simular búsqueda de disponibilidad
        # En una aplicación real, aquí consultarías la base de datos
        available_rooms = [
            {
                'id': 1,
                'name': 'Habitación Deluxe',
                'price': 299,
                'available': True,
                'image': '/static/images/room-deluxe.jpg'
            },
            {
                'id': 2,
                'name': 'Suite Premium',
                'price': 499,
                'available': True,
                'image': '/static/images/room-suite.jpg'
            },
            {
                'id': 3,
                'name': 'Suite Presidencial',
                'price': 899,
                'available': True,
                'image': '/static/images/room-presidential.jpg'
            }
        ]
        
        return JsonResponse({
            'success': True,
            'message': 'Habitaciones disponibles encontradas',
            'rooms': available_rooms,
            'checkin': checkin,
            'checkout': checkout,
            'guests': guests,
            'nights': (checkout_date - checkin_date).days
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Datos inválidos'
        }, status=400)
    except ValueError:
        return JsonResponse({
            'success': False,
            'message': 'Formato de fecha inválido'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Error interno del servidor'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def contact_form(request):
    """
    API endpoint para manejar el formulario de contacto
    """
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        message = data.get('message', '').strip()
        
        # Validaciones básicas
        if not name or not email or not message:
            return JsonResponse({
                'success': False,
                'message': 'Por favor, completa todos los campos requeridos'
            }, status=400)
        
        # Aquí normalmente guardarías en la base de datos y/o enviarías un email
        # Por ahora solo simulamos el procesamiento
        
        return JsonResponse({
            'success': True,
            'message': 'Mensaje enviado correctamente. Te contactaremos pronto.'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Datos inválidos'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Error interno del servidor'
        }, status=500)
from administracion.models import Plan, Promocion

def planes_list(request):
    planes = Plan.objects.all()
    return render(request, "planes_lista.html", {"planes": planes})

def promociones_list(request):
    promociones = Promocion.objects.all()
    return render(request, "promociones_lista.html", {"promociones": promociones})

def detalle_plan(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    return render(request, 'detalle_plan.html', {'plan': plan})

def promocion_detalle(request, promocion_id):
    promocion = get_object_or_404(Promocion, id=promocion_id)
    today = timezone.now().date()
    is_active = promocion.fecha_inicio <= today <= promocion.fecha_fin
    estado = 'activa' if is_active else ('proxima' if today < promocion.fecha_inicio else 'finalizada')
    dias_restantes = (promocion.fecha_fin - today).days if is_active else 0
    dias_para_inicio = (promocion.fecha_inicio - today).days if today < promocion.fecha_inicio else 0
    return render(request, 'promocion_detalle.html', {
        'promocion': promocion,
        'estado': estado,
        'dias_restantes': dias_restantes,
        'dias_para_inicio': dias_para_inicio,
    })

def servicio_detalle(request, servicio_id):
    servicio = get_object_or_404(Servicio, id=servicio_id)
    return render(request, 'servicio_detalle.html', {'servicio': servicio})

@login_required
def planes_y_promociones(request):
    planes = Plan.objects.all()
    promociones = Promocion.objects.all()
    return render(request, 'planes_promociones.html', {
        'planes': planes,
        'promociones': promociones
    })

# ===============================
# Reservar un Plan
# ===============================
@require_login_and_not_blocked
def reservar_plan(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)

    reserva = Reserva.objects.create(
        usuario=request.user,
        tipo_habitacion=plan.habitacion.tipo_habitacion,
        cantidad_habitaciones=1,
        plan=plan,
    )

    request.session['reserva_id'] = reserva.id
    return render(request, 'reservas/preguntar_servicios.html', {
        'reserva_id': reserva.id,
        'plan': plan,
    })


# ===============================
# Reservar una Promoción
# ===============================
@require_login_and_not_blocked
def reservar_promocion(request, promocion_id):
    promocion = get_object_or_404(Promocion, id=promocion_id)

    habitacion_id = request.session.get("habitacion_id")
    if not habitacion_id:
        return redirect("habitaciones_explorar")

    habitacion = get_object_or_404(Habitacion, id=habitacion_id)

    reserva = Reserva.objects.create(
        usuario=request.user,
        tipo_habitacion=habitacion.tipo_habitacion,
        cantidad_habitaciones=1,
        promocion=promocion,
    )

    return redirect("confirmar_reserva", reserva_id=reserva.id)


def instalaciones(request):
    """
    Página con información detallada sobre las instalaciones del hotel.
    """
    context = {
        'page_title': 'Instalaciones - Hotel',
        'meta_description': 'Conoce en detalle nuestras instalaciones: estacionamiento, piscinas, gimnasio, spa y más.'
    }
    return render(request, 'instalaciones.html', context)
