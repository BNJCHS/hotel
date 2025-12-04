
from django.shortcuts import render, get_object_or_404
from .models import Habitacion, TipoHabitacion
from decimal import Decimal

# Listado público con filtros
def lista_habitaciones_publica(request):
    habitaciones = Habitacion.objects.select_related('tipo_habitacion').all()

    # Parámetros de filtro
    tipo = request.GET.get('tipo', '').strip()
    capacidad_min = request.GET.get('capacidad_min', '').strip()
    precio_min = request.GET.get('precio_min', '').strip()
    precio_max = request.GET.get('precio_max', '').strip()
    solo_disponibles = request.GET.get('solo_disponibles', '').strip()

    # Aplicar filtros
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

    # Tipos disponibles para ayudar al usuario (listado de nombres únicos)
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


def detalle_habitacion_publica(request, id):
    habitacion = get_object_or_404(Habitacion, id=id)
    return render(request, 'habitaciones/detalle_habitacion.html', {
        'habitacion': habitacion
    })

# Detalle de tipo de habitación (público)
def detalle_tipo_publico(request, id):
    tipo = get_object_or_404(TipoHabitacion, id=id)
    return render(request, 'habitaciones/detalle_tipo.html', {
        'tipo': tipo
    })

from django.shortcuts import render, get_object_or_404, redirect
from .models import Habitacion, TipoHabitacion
from .forms import HabitacionAdminForm, TipoHabitacionForm

# Listado de habitaciones para administración
def admin_habitaciones_list(request):
    tipos = TipoHabitacion.objects.all().order_by('nombre')
    return render(request, 'administracion/habitaciones_list.html', {'tipos': tipos})

# Crear nueva habitación (admin)
def admin_habitaciones_create(request):
    # Cambiamos el flujo: este formulario ahora crea Tipos de Habitación, no Habitaciones individuales
    if request.method == 'POST':
        form = TipoHabitacionForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('habitaciones:habitaciones_list')
    else:
        form = TipoHabitacionForm()
    return render(request, 'administracion/habitaciones_form.html', {'form': form, 'titulo': 'Nuevo Tipo de Habitación'})

# Editar habitación (admin)
def admin_habitaciones_edit(request, pk):
    tipo = get_object_or_404(TipoHabitacion, pk=pk)
    if request.method == 'POST':
        form = TipoHabitacionForm(request.POST, request.FILES, instance=tipo)
        if form.is_valid():
            form.save()
            return redirect('habitaciones:habitaciones_list')
    else:
        form = TipoHabitacionForm(instance=tipo)
    return render(request, 'administracion/habitaciones_form.html', {'form': form, 'titulo': 'Editar Tipo de Habitación'})

# Eliminar habitación (admin)
def admin_habitaciones_delete(request, pk):
    tipo = get_object_or_404(TipoHabitacion, pk=pk)
    if request.method == 'POST':
        tipo.delete()
        return redirect('habitaciones:habitaciones_list')
    return render(request, 'administracion/habitacion_confirm_delete.html', {'tipo': tipo})


