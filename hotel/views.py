from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime, timedelta

def index(request):
    return render(request, 'index.html')

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
