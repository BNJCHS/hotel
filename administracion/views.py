# administracion/views.py
from django.shortcuts import render, redirect, get_object_or_404
from habitaciones.models import Habitacion
from .forms import HabitacionForm

def dashboard(request):
    return render(request, 'administracion/dashboard.html')

def lista_habitaciones_admin(request):
    habitaciones = Habitacion.objects.all()
    return render(request, 'administracion/habitaciones_admin.html', {
        'habitaciones': habitaciones
    })

def detalle_habitacion_admin(request, id):
    habitacion = get_object_or_404(Habitacion, id=id)
    return render(request, 'administracion/detalle_habitacion_admin.html', {
        'habitacion': habitacion
    })

# CREAR
def crear_habitacion(request):
    if request.method == 'POST':
        form = HabitacionForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('lista_habitaciones_admin')
    else:
        form = HabitacionForm()
    return render(request, 'administracion/form_habitacion.html', {'form': form, 'accion': 'Crear'})

# EDITAR
def editar_habitacion(request, id):
    habitacion = get_object_or_404(Habitacion, id=id)
    if request.method == 'POST':
        form = HabitacionForm(request.POST, request.FILES, instance=habitacion)
        if form.is_valid():
            form.save()
            return redirect('lista_habitaciones_admin')
    else:
        form = HabitacionForm(instance=habitacion)
    return render(request, 'administracion/form_habitacion.html', {'form': form, 'accion': 'Editar'})

# ELIMINAR
def eliminar_habitacion(request, id):
    habitacion = get_object_or_404(Habitacion, id=id)
    if request.method == 'POST':
        habitacion.delete()
        return redirect('lista_habitaciones_admin')
    return render(request, 'administracion/confirmar_eliminar.html', {'habitacion': habitacion})
