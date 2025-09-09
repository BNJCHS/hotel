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
import json
from datetime import datetime, timedelta
from decimal import Decimal

def lista_habitaciones(request):
    habitaciones = Habitacion.objects.all()  # Todas las habitaciones
    context = {
        'habitaciones': habitaciones
    }
    return render(request, 'lista_habitaciones.html', context)
def habitacion_detalle(request, id):
    habitacion = get_object_or_404(Habitacion, id=id)
    context = {
        'habitacion': habitacion
    }
    return render(request, 'habitacion_detalle.html', context)

# vistas.py
def seleccionar_habitacion(request, habitacion_id):
    request.session['habitacion_id'] = habitacion_id
    return redirect('seleccionar_fechas')


def index(request):
    planes = Plan.objects.all()[:3]  # Los primeros 3 planes
    promociones = Promocion.objects.all()[:3]  # Las primeras 3 promociones
    context = {
        'planes': planes,
        'promociones': promociones
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
    return render(request, 'promocion_detalle.html', {'promocion': promocion})

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
@login_required
def reservar_plan(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)

    # Crear la reserva con el plan
    reserva = Reserva.objects.create(
        usuario=request.user,
        habitacion=plan.habitacion,  # el plan ya tiene una habitación asociada
        plan=plan,
        confirmada=False
    )

    # Redirigir a confirmar la reserva con el ID
    return redirect("confirmar_reserva", reserva_id=reserva.id)


# ===============================
# Reservar una Promoción
# ===============================
@login_required
def reservar_promocion(request, promocion_id):
    promocion = get_object_or_404(Promocion, id=promocion_id)

    # ⚠️ Supongo que ya elegiste la habitación antes
    habitacion_id = request.session.get("habitacion_id")
    if not habitacion_id:
        return redirect("seleccionar_habitacion")

    habitacion = get_object_or_404(Habitacion, id=habitacion_id)

    # Crear la reserva con la promoción
    reserva = Reserva.objects.create(
        usuario=request.user,
        habitacion=habitacion,
        promocion=promocion,
        confirmada=False
    )

    # Redirigir a confirmar la reserva con el ID
    return redirect("confirmar_reserva", reserva_id=reserva.id)