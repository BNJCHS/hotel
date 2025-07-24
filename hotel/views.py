
from django.shortcuts import render, get_object_or_404, redirect
from .models import Habitacion, Reserva, Cliente
from .forms import ReservaForm
from django.db.models import Q
from datetime import datetime
def index(request):
    return render(request, 'index.html')
def buscar_habitaciones(request):
    habitaciones_disponibles = None
    fecha_entrada = request.GET.get('fecha_entrada')
    fecha_salida = request.GET.get('fecha_salida')

    if fecha_entrada and fecha_salida:
        try:
            entrada = datetime.strptime(fecha_entrada, "%Y-%m-%d").date()
            salida = datetime.strptime(fecha_salida, "%Y-%m-%d").date()
            # Habitaciones reservadas en esas fechas
            reservas = Reserva.objects.filter(
                Q(fecha_entrada__lt=salida) & Q(fecha_salida__gt=entrada)
            )
            habitaciones_ocupadas_ids = reservas.values_list('habitacion_id', flat=True)
            habitaciones_disponibles = Habitacion.objects.exclude(id__in=habitaciones_ocupadas_ids)
        except ValueError:
            habitaciones_disponibles = Habitacion.objects.none()
    context = {
        'habitaciones_disponibles': habitaciones_disponibles,
        'fecha_entrada': fecha_entrada,
        'fecha_salida': fecha_salida
    }
    return render(request, 'hotel/index.html', context)


def reservar(request, habitacion_id):
    habitacion = get_object_or_404(Habitacion, id=habitacion_id)
    fecha_entrada = request.GET.get('entrada')
    fecha_salida = request.GET.get('salida')

    if request.method == 'POST':
        form = ReservaForm(request.POST)
        if form.is_valid():
            # Validar que la habitación esté disponible
            entrada = form.cleaned_data['fecha_entrada']
            salida = form.cleaned_data['fecha_salida']
            # Chequear que no se cruce con otras reservas
            conflictivas = Reserva.objects.filter(
                habitacion=habitacion,
                fecha_entrada__lt=salida,
                fecha_salida__gt=entrada
            )
            if conflictivas.exists():
                form.add_error(None, "La habitación no está disponible en esas fechas.")
            else:
                # Crear o buscar cliente
                cliente, created = Cliente.objects.get_or_create(
                    email=form.cleaned_data['email'],
                    defaults={
                        'nombre': form.cleaned_data['nombre'],
                        'apellido': form.cleaned_data['apellido'],
                        'telefono': form.cleaned_data['telefono'],
                    }
                )
                # Crear reserva
                reserva = Reserva.objects.create(
                    habitacion=habitacion,
                    cliente=cliente,
                    fecha_entrada=entrada,
                    fecha_salida=salida
                )
                return render(request, 'hotel/confirmacion.html', {'reserva': reserva})
    else:
        initial = {}
        if fecha_entrada and fecha_salida:
            initial = {'fecha_entrada': fecha_entrada, 'fecha_salida': fecha_salida}
        form = ReservaForm(initial=initial)

    return render(request, 'hotel/reservar.html', {'form': form, 'habitacion': habitacion})
