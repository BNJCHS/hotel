# administracion/views.py
from django.shortcuts import render, redirect, get_object_or_404
from habitaciones.models import Habitacion
from .forms import HabitacionForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.utils import timezone
from .models import *
from .forms import *
from .decorators import role_required
from .forms import HuespedForm 
import json

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if hasattr(user, 'userprofile') and user.userprofile.activo:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Usuario inactivo. Contacte al administrador.')
        else:
            messages.error(request, 'Credenciales inválidas.')
    
    return render(request, 'login.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    # Estadísticas generales
    total_clientes = Cliente.objects.filter(activo=True).count()
    total_empleados = Empleado.objects.filter(activo=True).count()
    total_servicios = Servicio.objects.filter(disponible=True).count()
    promociones_activas = Promocion.objects.filter(activa=True).count()
    
    # Datos para gráficos
    clientes_por_mes = Cliente.objects.extra(
        select={'month': 'EXTRACT(month FROM fecha_registro)'}
    ).values('month').annotate(count=Count('id')).order_by('month')
    
    context = {
        'total_clientes': total_clientes,
        'total_empleados': total_empleados,
        'total_servicios': total_servicios,
        'promociones_activas': promociones_activas,
        'clientes_por_mes': list(clientes_por_mes),
        'user_role': request.user.userprofile.role if hasattr(request.user, 'userprofile') else 'admin'
    }
    
    return render(request, 'dashboard.html', context)

# CLIENTES
@login_required
@role_required(['admin', 'recepcionista', 'gerente'])
def clientes_list(request):
    search = request.GET.get('search', '')
    clientes = Cliente.objects.filter(activo=True)
    
    if search:
        clientes = clientes.filter(
            Q(nombre__icontains=search) |
            Q(apellido__icontains=search) |
            Q(email__icontains=search) |
            Q(cedula__icontains=search)
        )
    
    paginator = Paginator(clientes, 10)
    page = request.GET.get('page')
    clientes = paginator.get_page(page)
    
    return render(request, 'clientes/list.html', {'clientes': clientes, 'search': search})

@login_required
@role_required(['admin', 'recepcionista', 'gerente'])
def cliente_create(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente creado exitosamente.')
            return redirect('clientes_list')
    else:
        form = ClienteForm()
    
    return render(request, 'clientes/form.html', {'form': form, 'title': 'Nuevo Cliente'})

@login_required
@role_required(['admin', 'recepcionista', 'gerente'])
def cliente_edit(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente actualizado exitosamente.')
            return redirect('clientes_list')
    else:
        form = ClienteForm(instance=cliente)
    
    return render(request, 'clientes/form.html', {'form': form, 'title': 'Editar Cliente'})

# HUÉSPEDES
@login_required
@role_required(['admin', 'recepcionista', 'gerente'])
def huesped_create(request):
    if request.method == 'POST':
        form = HuespedForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Huésped creado exitosamente.')
            return redirect('huespedes_list')
    else:
        form = HuespedForm()
    
    return render(request, 'huespedes/form.html', {
        'form': form,
        'title': 'Nuevo Huésped'
    })

@login_required
@role_required(['admin', 'recepcionista', 'gerente'])
def huespedes_list(request):
    search = request.GET.get('search', '')
    huespedes = Huesped.objects.all()
    
    if search:
        huespedes = huespedes.filter(
            Q(nombre__icontains=search) |
            Q(apellido__icontains=search) |
            Q(email__icontains=search) |
            Q(cedula__icontains=search)
        )
    
    paginator = Paginator(huespedes, 10)
    page = request.GET.get('page')
    huespedes = paginator.get_page(page)
    
    return render(request, 'huespedes/list.html', {'huespedes': huespedes, 'search': search})


@login_required
@role_required(['admin', 'recepcionista', 'gerente'])
def huesped_edit(request, pk):
    huesped = get_object_or_404(Huesped, pk=pk)
    
    if request.method == 'POST':
        form = HuespedForm(request.POST, instance=huesped)
        if form.is_valid():
            form.save()
            messages.success(request, 'Huésped actualizado exitosamente.')
            return redirect('huespedes_list')
    else:
        form = HuespedForm(instance=huesped)
    
    return render(request, 'huespedes/form.html', {'form': form, 'title': 'Editar Huésped'})


# SERVICIOS
@login_required
@role_required(['admin', 'gerente'])
def servicios_list(request):
    categoria = request.GET.get('categoria', '')
    servicios = Servicio.objects.all()
    
    if categoria:
        servicios = servicios.filter(categoria=categoria)
    
    categorias = Servicio.CATEGORIAS
    
    return render(request, 'servicios/list.html', {
        'servicios': servicios,
        'categorias': categorias,
        'selected_categoria': categoria
    })

@login_required
@role_required(['admin', 'gerente'])
def servicio_edit(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    
    if request.method == 'POST':
        form = ServicioForm(request.POST, instance=servicio)
        if form.is_valid():
            form.save()
            messages.success(request, 'Servicio actualizado exitosamente.')
            return redirect('servicios_list')
    else:
        form = ServicioForm(instance=servicio)
    
    return render(request, 'servicios/form.html', {
        'form': form,
        'title': 'Editar Servicio'
    })

@login_required
@role_required(['admin', 'gerente'])
def servicio_create(request):
    if request.method == 'POST':
        form = ServicioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Servicio creado exitosamente.')
            return redirect('servicios_list')
    else:
        form = ServicioForm()
    
    return render(request, 'servicios/form.html', {'form': form, 'title': 'Nuevo Servicio'})

@login_required
@role_required(['admin', 'gerente'])
def toggle_servicio_disponibilidad(request, pk):
    """Activa/Desactiva un servicio vía AJAX o POST normal"""
    servicio = get_object_or_404(Servicio, pk=pk)

    if request.method == 'POST':
        servicio.disponible = not servicio.disponible
        servicio.save()
        messages.success(
            request,
            f"El servicio '{servicio.nombre}' ahora está {'disponible' if servicio.disponible else 'no disponible'}."
        )
        return redirect('servicios_list')

    return render(request, 'servicios/confirmar_toggle.html', {
        'servicio': servicio
    })


# EMPLEADOS
@login_required
@role_required(['admin', 'gerente'])
def empleados_list(request):
    departamento = request.GET.get('departamento', '')
    empleados = Empleado.objects.filter(activo=True)
    
    if departamento:
        empleados = empleados.filter(departamento=departamento)
    
    departamentos = Empleado.DEPARTAMENTOS
    
    return render(request, 'empleados/list.html', {
        'empleados': empleados,
        'departamentos': departamentos,
        'selected_departamento': departamento
    })

@login_required
@role_required(['admin', 'gerente'])
def empleado_create(request):
    if request.method == 'POST':
        form = EmpleadoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Empleado creado exitosamente.')
            return redirect('empleados_list')
    else:
        form = EmpleadoForm()
    
    return render(request, 'empleados/form.html', {
        'form': form,
        'title': 'Nuevo Empleado'
    })


@login_required
@role_required(['admin', 'gerente'])
def empleado_edit(request, pk):
    empleado = get_object_or_404(Empleado, pk=pk)
    
    if request.method == 'POST':
        form = EmpleadoForm(request.POST, instance=empleado)
        if form.is_valid():
            form.save()
            messages.success(request, 'Empleado actualizado exitosamente.')
            return redirect('empleados_list')
    else:
        form = EmpleadoForm(instance=empleado)
    
    return render(request, 'empleados/form.html', {
        'form': form,
        'title': 'Editar Empleado'
    })

# PLANES DE HOSPEDAJE
@login_required
@role_required(['admin', 'gerente'])
def planes_list(request):
    tipo = request.GET.get('tipo', '')
    planes = PlanHospedaje.objects.filter(activo=True)
    
    if tipo:
        planes = planes.filter(tipo=tipo)
    
    tipos = PlanHospedaje.TIPOS
    
    return render(request, 'planes/list.html', {
        'planes': planes,
        'tipos': tipos,
        'selected_tipo': tipo
    })

# PROMOCIONES
@login_required
@role_required(['admin', 'gerente'])
def promociones_list(request):
    promociones = Promocion.objects.all().order_by('-fecha_inicio')
    
    return render(request, 'promociones/list.html', {'promociones': promociones})

@login_required
@role_required(['admin', 'gerente'])
def promocion_create(request):
    if request.method == 'POST':
        form = PromocionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Promoción creada exitosamente.')
            return redirect('promociones_list')
    else:
        form = PromocionForm()
    
    return render(request, 'promociones/form.html', {'form': form, 'title': 'Nueva Promoción'})

# API ENDPOINTS
@login_required
def api_stats(request):
    """API endpoint para estadísticas del dashboard"""
    stats = {
        'clientes_total': Cliente.objects.filter(activo=True).count(),
        'empleados_total': Empleado.objects.filter(activo=True).count(),
        'servicios_total': Servicio.objects.filter(disponible=True).count(),
        'promociones_activas': Promocion.objects.filter(activa=True).count(),
    }
    
    return JsonResponse(stats)

@login_required
def toggle_servicio_disponibilidad(request, pk):
    """Toggle disponibilidad de servicio via AJAX"""
    if request.method == 'POST':
        servicio = get_object_or_404(Servicio, pk=pk)
        servicio.disponible = not servicio.disponible
        servicio.save()
        
        return JsonResponse({
            'success': True,
            'disponible': servicio.disponible
        })
    
    return JsonResponse({'success': False})

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
