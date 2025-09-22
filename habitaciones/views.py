
from django.shortcuts import render, get_object_or_404
from .models import Habitacion

def lista_habitaciones_publica(request):
    habitaciones = Habitacion.objects.all()
    return render(request, 'habitaciones/listar_habitaciones.html', {
        'habitaciones': habitaciones
    })

def detalle_habitacion_publica(request, id):
    habitacion = get_object_or_404(Habitacion, id=id)
    return render(request, 'habitaciones/detalle_habitacion.html', {
        'habitacion': habitacion
    })

from django.shortcuts import render, get_object_or_404, redirect
from .models import Habitacion
-from .forms import HabitacionAdminForm
+from .forms import HabitacionAdminForm, TipoHabitacionForm

# Listado de habitaciones para administración
def admin_habitaciones_list(request):
    habitaciones = Habitacion.objects.all()
    return render(request, 'administracion/habitaciones_list.html', {'habitaciones': habitaciones})

# Crear nueva habitación (admin)
def admin_habitaciones_create(request):
-    if request.method == 'POST':
-        form = HabitacionAdminForm(request.POST, request.FILES)
-        if form.is_valid():
-            form.save()
-            return redirect('habitaciones:habitaciones_list')
-    else:
-        form = HabitacionAdminForm()
-    return render(request, 'administracion/habitaciones_form.html', {'form': form, 'titulo': 'Nueva Habitación'})
+    # Cambiamos el flujo: este formulario ahora crea Tipos de Habitación, no Habitaciones individuales
+    if request.method == 'POST':
+        form = TipoHabitacionForm(request.POST, request.FILES)
+        if form.is_valid():
+            form.save()
+            return redirect('habitaciones:habitaciones_list')
+    else:
+        form = TipoHabitacionForm()
+    return render(request, 'administracion/habitaciones_form.html', {'form': form, 'titulo': 'Nuevo Tipo de Habitación'})

# Editar habitación (admin)
def admin_habitaciones_edit(request, pk):
    habitacion = get_object_or_404(Habitacion, pk=pk)
    if request.method == 'POST':
        form = HabitacionAdminForm(request.POST, request.FILES, instance=habitacion)
        if form.is_valid():
            form.save()
            return redirect('habitaciones:habitaciones_list')
    else:
        form = HabitacionAdminForm(instance=habitacion)
    return render(request, 'administracion/habitaciones_form.html', {'form': form, 'titulo': 'Editar Habitación'})

# Eliminar habitación (admin)
def admin_habitaciones_delete(request, pk):
    habitacion = get_object_or_404(Habitacion, pk=pk)
    if request.method == 'POST':
        habitacion.delete()
        return redirect('habitaciones:habitaciones_list')
    return render(request, 'administracion/habitacion_confirm_delete.html', {'habitacion': habitacion})


