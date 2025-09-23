from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.urls import reverse
from reservas.models import Reserva
from .models import Empleado, Plan, Promocion, Servicio, Huesped, Rol, UsuarioRol, Permiso, RolPermiso
from .forms import EmpleadoForm, PlanForm, PromocionForm, ServicioForm, HuespedForm, AdminLoginForm
from reservas.models import Huesped as ReservaHuesped
from django.http import JsonResponse

from django.db.models import Sum
# imports relacionados con reservas/huespedes
from reservas.models import Reserva, HuespedActivo

# imports de la app administracion
from .models import Empleado, Plan, Promocion, Servicio  # NOTAR: no importamos Huesped de administracion para evitar choque de nombres
from .forms import EmpleadoForm, PlanForm, PromocionForm, ServicioForm, HuespedForm

# imports para gestión de usuarios
from django.contrib.auth.models import User
from usuarios.models import Profile

# para control de accesos en las vistas
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST

# imports para el sistema de permisos
from .permissions import (
    requiere_staff_y_permiso, 
    requiere_permiso, 
    usuario_tiene_permiso,
    obtener_permisos_usuario
)

# ===== VISTAS DE AUTENTICACIÓN PARA ADMINISTRACIÓN =====

@csrf_protect
@never_cache
def admin_login(request):
    """Vista de login específica para administración"""
    # Si el usuario ya está autenticado y es staff, redirigir al dashboard
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('administracion:dashboard')
    
    if request.method == 'POST':
        form = AdminLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Bienvenido al panel de administración, {user.get_full_name() or user.username}')
            
            # Redirigir a la página solicitada o al dashboard
            next_url = request.GET.get('next', reverse('administracion:dashboard'))
            return redirect(next_url)
        else:
            messages.error(request, 'Error en el login. Verifica tus credenciales.')
    else:
        form = AdminLoginForm(request)
    
    return render(request, 'administracion/login.html', {
        'form': form,
        'title': 'Login Administración'
    })


@login_required
def admin_logout(request):
    """Vista de logout específica para administración"""
    if request.user.is_staff:
        username = request.user.get_full_name() or request.user.username
        logout(request)
        messages.success(request, f'Has cerrado sesión correctamente, {username}')
    else:
        logout(request)
    
    return redirect('administracion:admin_login')


@login_required
@requiere_staff_y_permiso('dashboard', 'ver')
def dashboard(request):
    """Dashboard principal de administración"""
    # Estadísticas básicas
    total_usuarios = User.objects.count()
    total_empleados = Empleado.objects.count()
    total_reservas = Reserva.objects.count()
    reservas_activas = Reserva.objects.filter(estado='activa').count()
    
    context = {
        'total_usuarios': total_usuarios,
        'total_empleados': total_empleados,
        'total_reservas': total_reservas,
        'reservas_activas': reservas_activas,
        'user_permissions': obtener_permisos_usuario(request.user),
    }
    
    return render(request, 'administracion/dashboard.html', context)

# ===== VISTAS DE GESTIÓN DE USUARIOS =====

@requiere_staff_y_permiso('usuarios', 'ver')
def usuarios_list(request):
    """Vista para listar todos los usuarios registrados"""
    usuarios = User.objects.select_related('profile').all().order_by('-date_joined')
    
    # Búsqueda de usuarios
    query = request.GET.get('q')
    if query:
        usuarios = usuarios.filter(
            Q(username__icontains=query) | 
            Q(email__icontains=query) | 
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query)
        )
    
    # Filtros de estado
    status_filter = request.GET.get('status')
    if status_filter == 'active':
        usuarios = usuarios.filter(is_active=True)
    elif status_filter == 'inactive':
        usuarios = usuarios.filter(is_active=False)
    
    # Filtros de bloqueo
    block_filter = request.GET.get('block_status')
    if block_filter == 'blocked':
        usuarios = usuarios.filter(profile__is_blocked=True)
    elif block_filter == 'not_blocked':
        usuarios = usuarios.filter(profile__is_blocked=False)
    
    # Filtros de tipo de usuario
    user_type_filter = request.GET.get('user_type')
    if user_type_filter == 'staff':
        usuarios = usuarios.filter(is_staff=True)
    elif user_type_filter == 'client':
        usuarios = usuarios.filter(is_staff=False)
    
    # Paginación
    paginator = Paginator(usuarios, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas para mostrar en el template
    total_usuarios = User.objects.count()
    usuarios_bloqueados = User.objects.filter(profile__is_blocked=True).count()
    usuarios_activos = User.objects.filter(is_active=True).count()
    
    return render(request, 'administracion/usuarios_list.html', {
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
        'block_filter': block_filter,
        'user_type_filter': user_type_filter,
        'total_usuarios': total_usuarios,
        'usuarios_bloqueados': usuarios_bloqueados,
        'usuarios_activos': usuarios_activos,
    })


@requiere_staff_y_permiso('usuarios', 'ver')
def usuario_detail(request, user_id):
    """Vista para ver el detalle de un usuario"""
    usuario = get_object_or_404(User, id=user_id)
    
    return render(request, 'administracion/usuario_detail.html', {
        'usuario': usuario
    })

@require_POST
def activar_reserva(request, reserva_id):
    """Activa una reserva y carga los huéspedes registrados por el usuario"""
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    # Activar la reserva (solo desde administración)
    reserva.activada = True
    reserva.save()
    
    # Cargar huéspedes desde la información guardada por el usuario
    huespedes = ReservaHuesped.objects.filter(reserva=reserva)
    
    # Crear huéspedes activos en el sistema
    for huesped in huespedes:
        HuespedActivo.objects.create(
            reserva=reserva,
            nombre=huesped.nombre,
            apellido=huesped.apellido,
            documento=huesped.documento,
            edad=huesped.edad,
            telefono=huesped.telefono if hasattr(huesped, 'telefono') else '',
            email=huesped.email if hasattr(huesped, 'email') else ''
        )
    
    messages.success(request, f'Reserva #{reserva_id} activada correctamente. {len(huespedes)} huéspedes registrados.')
    return JsonResponse({'status': 'success', 'message': 'Reserva activada correctamente'})

@requiere_staff_y_permiso('dashboard', 'ver')
def dashboard(request):
    from datetime import datetime, timedelta
    from django.db.models import Count, Q
    from habitaciones.models import Habitacion
    from reservas.models import HuespedActivo
    
    # Verificar permisos específicos para mostrar información
    context = {}
    
    # Fechas para filtros
    hoy = timezone.now().date()
    hace_30_dias = hoy - timedelta(days=30)
    hace_7_dias = hoy - timedelta(days=7)
    
    # Obtener estadísticas básicas
    total_usuarios = User.objects.count()
    context['total_usuarios'] = total_usuarios
    
    if usuario_tiene_permiso(request.user, 'reservas', 'ver'):
        # Estadísticas básicas de reservas
        context["total_reservas"] = Reserva.objects.count()
        context["total_ingresos"] = Reserva.objects.aggregate(total=Sum("monto"))["total"] or 0
        context["reservas"] = Reserva.objects.order_by("-fecha_reserva")[:5]
        
        # Reservas por estado
        context["reservas_pendientes"] = Reserva.objects.filter(estado='pendiente').count()
        context["reservas_confirmadas"] = Reserva.objects.filter(estado='confirmada').count()
        context["reservas_activas"] = Reserva.objects.filter(estado='activa').count()
        
        # Ingresos del mes
        context["ingresos_mes"] = Reserva.objects.filter(
            fecha_reserva__gte=hace_30_dias
        ).aggregate(total=Sum("monto"))["total"] or 0
        
        # Datos para gráficos - Reservas por día (últimos 7 días)
        reservas_por_dia = []
        labels_dias = []
        for i in range(7):
            dia = hoy - timedelta(days=i)
            count = Reserva.objects.filter(fecha_reserva__date=dia).count()
            reservas_por_dia.insert(0, count)
            labels_dias.insert(0, dia.strftime('%d/%m'))
        
        context["chart_reservas_labels"] = labels_dias
        context["chart_reservas_data"] = reservas_por_dia
        
        # Reservas por tipo de habitación
        reservas_por_tipo = Reserva.objects.values('tipo_habitacion__nombre').annotate(
            count=Count('id')
        ).order_by('-count')
        
        context["chart_tipos_labels"] = [item['tipo_habitacion__nombre'] for item in reservas_por_tipo]
        context["chart_tipos_data"] = [item['count'] for item in reservas_por_tipo]
    
    if usuario_tiene_permiso(request.user, 'huespedes', 'ver'):
        context['total_huespedes'] = Huesped.objects.count()
        context['huespedes_activos'] = HuespedActivo.objects.filter(activo=True).count()
    
    if usuario_tiene_permiso(request.user, 'empleados', 'ver'):
        context["total_empleados"] = Empleado.objects.count()
    
    if usuario_tiene_permiso(request.user, 'habitaciones', 'ver'):
        # Estadísticas de habitaciones
        total_habitaciones = Habitacion.objects.count()
        habitaciones_disponibles = Habitacion.objects.filter(disponible=True).count()
        habitaciones_ocupadas = total_habitaciones - habitaciones_disponibles
        
        context["total_habitaciones"] = total_habitaciones
        context["habitaciones_disponibles"] = habitaciones_disponibles
        context["habitaciones_ocupadas"] = habitaciones_ocupadas
        context["ocupacion_porcentaje"] = round((habitaciones_ocupadas / total_habitaciones * 100) if total_habitaciones > 0 else 0, 1)
        
        # Habitaciones por tipo
        habitaciones_por_tipo = Habitacion.objects.values('tipo_habitacion__nombre').annotate(
            total=Count('id'),
            disponibles=Count('id', filter=Q(disponible=True))
        )
        context["habitaciones_por_tipo"] = habitaciones_por_tipo
    
    # Agregar permisos del usuario al contexto
    from .permissions import convertir_permisos_para_template
    permisos_raw = obtener_permisos_usuario(request.user)
    context['permisos'] = convertir_permisos_para_template(permisos_raw)
    
    return render(request, "administracion/dashboard.html", context)

# ===== Helpers =====
def _paginate(request, queryset, per_page=10):
    page_number = request.GET.get("page")
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(page_number)

# ===================== EMPLEADOS =====================
@requiere_staff_y_permiso('empleados', 'ver')
def empleados_list(request):
    q = request.GET.get("q", "")
    qs = Empleado.objects.all()
    if q:
        qs = qs.filter(
            Q(nombre__icontains=q) | Q(apellido__icontains=q) | Q(dni__icontains=q) | Q(puesto__icontains=q)
        )
    page_obj = _paginate(request, qs, 10)
    return render(request, "administracion/empleados_list.html", {"page_obj": page_obj, "q": q})

@requiere_staff_y_permiso('empleados', 'crear')
def empleados_create(request):
    if request.method == "POST":
        form = EmpleadoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Empleado creado correctamente.")
            return redirect("empleados_list")
    else:
        form = EmpleadoForm()
    return render(request, "administracion/empleados_form.html", {"form": form})

@requiere_staff_y_permiso('empleados', 'editar')
def empleados_edit(request, pk):
    obj = get_object_or_404(Empleado, pk=pk)
    if request.method == "POST":
        form = EmpleadoForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Empleado actualizado.")
            return redirect("empleados_list")
    else:
        form = EmpleadoForm(instance=obj)
    return render(request, "administracion/empleados_form.html", {"form": form})

@requiere_staff_y_permiso('empleados', 'eliminar')
def empleados_delete(request, pk):
    obj = get_object_or_404(Empleado, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Empleado eliminado.")
        return redirect("empleados_list")
    return render(request, "administracion/empleados_confirm_delete.html", {"empleado": obj})

# ===================== PLANES =====================
@requiere_staff_y_permiso('planes', 'ver')
def planes_list(request):
    q = request.GET.get("q", "")
    qs = Plan.objects.all()
    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(descripcion__icontains=q))
    page_obj = _paginate(request, qs, 10)
    return render(request, "administracion/planes_list.html", {"page_obj": page_obj, "q": q})

@requiere_staff_y_permiso('planes', 'crear')
def planes_create(request):
    if request.method == "POST":
        form = PlanForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Plan creado correctamente.")
            return redirect("administracion:planes_list")
    else:
        form = PlanForm()
    return render(request, "administracion/planes_form.html", {"form": form})

@requiere_staff_y_permiso('planes', 'editar')
def planes_edit(request, pk):
    obj = get_object_or_404(Plan, pk=pk)
    if request.method == "POST":
        form = PlanForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Plan actualizado.")
            return redirect("administracion:planes_list")
    else:
        form = PlanForm(instance=obj)
    return render(request, "administracion/planes_form.html", {"form": form})

@requiere_staff_y_permiso('planes', 'eliminar')
def planes_delete(request, pk):
    obj = get_object_or_404(Plan, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Plan eliminado.")
        return redirect("administracion:planes_list")
    return render(request, "administracion/planes_confirm_delete.html", {"plan": obj})

# ===================== PROMOCIONES =====================
@requiere_staff_y_permiso('promociones', 'ver')
def promociones_list(request):
    q = request.GET.get("q", "")
    qs = Promocion.objects.all()
    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(descripcion__icontains=q))
    page_obj = _paginate(request, qs, 10)
    return render(request, "administracion/promociones_list.html", {"page_obj": page_obj, "q": q})

@requiere_staff_y_permiso('promociones', 'crear')
def promociones_create(request):
    if request.method == "POST":
        form = PromocionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Promoción creada correctamente.")
            return redirect("administracion:promociones_list")
    else:
        form = PromocionForm()
    return render(request, "administracion/promociones_form.html", {"form": form})

@requiere_staff_y_permiso('promociones', 'editar')
def promociones_edit(request, pk):
    obj = get_object_or_404(Promocion, pk=pk)
    if request.method == "POST":
        form = PromocionForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Promoción actualizada.")
            return redirect("administracion:promociones_list")
    else:
        form = PromocionForm(instance=obj)
    return render(request, "administracion/promociones_form.html", {"form": form})

@requiere_staff_y_permiso('promociones', 'eliminar')
def promociones_delete(request, pk):
    obj = get_object_or_404(Promocion, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Promoción eliminada.")
        return redirect("administracion:promociones_list")
    return render(request, "administracion/promociones_confirm_delete.html", {"promocion": obj})

# ===================== SERVICIOS =====================
@requiere_staff_y_permiso('servicios', 'ver')
def servicios_list(request):
    q = request.GET.get("q", "")
    qs = Servicio.objects.all()
    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(descripcion__icontains=q))
    page_obj = _paginate(request, qs, 10)
    return render(request, "administracion/servicios_list.html", {"page_obj": page_obj, "q": q})

@requiere_staff_y_permiso('servicios', 'crear')
def servicios_create(request):
    if request.method == "POST":
        form = ServicioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Servicio creado correctamente.")
            return redirect("administracion:servicios_list")
    else:
        form = ServicioForm()
    return render(request, "administracion/servicios_form.html", {"form": form})

@requiere_staff_y_permiso('servicios', 'editar')
def servicios_edit(request, pk):
    obj = get_object_or_404(Servicio, pk=pk)
    if request.method == "POST":
        form = ServicioForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Servicio actualizado.")
            return redirect("administracion:servicios_list")
    else:
        form = ServicioForm(instance=obj)
    return render(request, "administracion/servicios_form.html", {"form": form})

@requiere_staff_y_permiso('servicios', 'eliminar')
def servicios_delete(request, pk):
    obj = get_object_or_404(Servicio, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Servicio eliminado.")
        return redirect("administracion:servicios_list")
    return render(request, "administracion/servicios_confirm_delete.html", {"servicio": obj})

# ===================== HUÉSPEDES =====================
@requiere_staff_y_permiso('huespedes', 'ver')
def huespedes_list(request):
    q = request.GET.get("q", "")
    qs = Huesped.objects.all()
    if q:
        qs = qs.filter(
            Q(nombre__icontains=q) | Q(apellido__icontains=q) | Q(dni__icontains=q) |
            Q(email__icontains=q) | Q(telefono__icontains=q)
        )
    page_obj = _paginate(request, qs, 10)
    return render(request, "administracion/huespedes_list.html", {"page_obj": page_obj, "q": q})

@requiere_staff_y_permiso('huespedes', 'crear')
def huespedes_create(request):
    if request.method == "POST":
        form = HuespedForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Huésped creado correctamente.")
            return redirect("huespedes_list")
    else:
        form = HuespedForm()
    return render(request, "administracion/huespedes_form.html", {"form": form})

@requiere_staff_y_permiso('huespedes', 'editar')
def huespedes_edit(request, pk):
    obj = get_object_or_404(Huesped, pk=pk)
    if request.method == "POST":
        form = HuespedForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Huésped actualizado.")
            return redirect("huespedes_list")
    else:
        form = HuespedForm(instance=obj)
    return render(request, "administracion/huespedes_form.html", {"form": form})

@requiere_staff_y_permiso('huespedes', 'eliminar')
def huespedes_delete(request, pk):
    obj = get_object_or_404(Huesped, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Huésped eliminado.")
        return redirect("huespedes_list")
    return render(request, "administracion/huespedes_confirm_delete.html", {"huesped": obj})

@requiere_staff_y_permiso('reservas', 'ver')
def ver_reservas(request):
    reservas = Reserva.objects.select_related('usuario', 'tipo_habitacion', 'habitacion_asignada', 'plan', 'promocion') \
                              .prefetch_related('servicios') \
                              .order_by('-fecha_reserva')
    return render(request, 'administracion/ver_reservas.html', {'reservas': reservas})

@requiere_staff_y_permiso('reservas', 'confirmar')
@require_POST
def confirmar_reserva_admin(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    if reserva.estado == 'confirmada':
        messages.info(request, "La reserva ya está confirmada.")
        return redirect('administracion:ver_reservas')

    reserva.estado = 'confirmada'
    reserva.save()

    # Creamos HuespedActivo para cada Huesped asociado a la reserva
    huespedes = reserva.huespedes.all()  # related_name definido en reservas.models.Huesped
    creados = 0
    for h in huespedes:
        # get_or_create evita duplicados si ya se creó antes
        obj, creado = HuespedActivo.objects.get_or_create(
            huesped=h,
            reserva=reserva,
            defaults={
                'habitacion': reserva.habitacion_asignada,  # Usar habitacion_asignada
                'fecha_checkin': reserva.check_in,
                'fecha_checkout': reserva.check_out
            }
        )
        if creado:
            creados += 1

    # Reservar las habitaciones del tipo solicitado
    tipo_habitacion = reserva.tipo_habitacion
    tipo_habitacion.reservar_stock(reserva.cantidad_habitaciones)

    messages.success(request, f"Reserva confirmada. {creados} huésped(es) activado(s).")
    return redirect('administracion:ver_reservas')


@requiere_staff_y_permiso('reservas', 'cancelar')
@require_POST
def rechazar_reserva_admin(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    if reserva.estado == 'confirmada':
        messages.error(request, "No se puede rechazar una reserva ya confirmada.")
    else:
        # opción A) eliminar la reserva:
        reserva.delete()
        messages.success(request, "Reserva rechazada y eliminada.")
        # opción B) podrías preferir marcar un campo 'rechazada' en lugar de borrarla
    return redirect('administracion/ver_reservas')


@requiere_staff_y_permiso('huespedes', 'ver')
def huespedes_activos(request):
    hoy = timezone.now().date()
    activos_qs = HuespedActivo.objects.filter(
        activo=True
    ).filter(
        Q(fecha_checkin__lte=hoy) | Q(fecha_checkin__isnull=True),
        Q(fecha_checkout__gte=hoy) | Q(fecha_checkout__isnull=True)
    ).select_related('huesped', 'reserva', 'habitacion')

    return render(request, 'administracion/huespedes_activos.html', {'activos': activos_qs})


@requiere_staff_y_permiso('huespedes', 'editar')
@require_POST
def finalizar_huesped_activo(request, activo_id):
    ha = get_object_or_404(HuespedActivo, id=activo_id)
    ha.finalizar()
    # Si no hay otros huéspedes activos en esa habitación, marcar disponible
    habit = ha.habitacion
    if habit:
        otras = HuespedActivo.objects.filter(habitacion=habit, activo=True).exclude(id=ha.id).exists()
        if not otras and hasattr(habit, 'disponible'):
            habit.disponible = True
            habit.save()
    messages.success(request, "Huésped finalizado (checkout).")
    return redirect('administracion/huespedes_activos')


# ============ GESTIÓN DE ROLES Y PERMISOS ============

@requiere_staff_y_permiso('roles', 'ver')
def roles_list(request):
    """Lista todos los roles con sus permisos y asignaciones"""
    from django.contrib.auth.models import User
    from django.db.models import Count
    
    roles = Rol.objects.annotate(
        usuarios_count=Count('usuarios')
    ).order_by('nombre')
    
    usuarios = User.objects.filter(is_active=True).order_by('username')
    
    asignaciones = UsuarioRol.objects.select_related('usuario', 'rol').order_by('usuario__username')
    
    # Crear matriz de permisos
    permisos_matriz = {}
    permisos_todos = Permiso.objects.all().order_by('modulo', 'accion')
    
    for permiso in permisos_todos:
        if permiso.modulo not in permisos_matriz:
            permisos_matriz[permiso.modulo] = []
        if permiso.accion not in permisos_matriz[permiso.modulo]:
            permisos_matriz[permiso.modulo].append(permiso.accion)
    
    # Obtener permisos por rol
    permisos_por_rol = {}
    for rol in roles:
        permisos_por_rol[rol.id] = {}
        rol_permisos = RolPermiso.objects.filter(rol=rol).select_related('permiso')
        for rp in rol_permisos:
            modulo = rp.permiso.modulo
            accion = rp.permiso.accion
            if modulo not in permisos_por_rol[rol.id]:
                permisos_por_rol[rol.id][modulo] = []
            permisos_por_rol[rol.id][modulo].append(accion)
    
    context = {
        'roles': roles,
        'usuarios': usuarios,
        'asignaciones': asignaciones,
        'permisos_matriz': permisos_matriz,
        'permisos_por_rol': permisos_por_rol,
    }
    
    return render(request, 'administracion/roles_list.html', context)


@requiere_staff_y_permiso('roles', 'asignar')
@require_POST
def asignar_rol(request):
    """Asigna un rol a un usuario"""
    from django.contrib.auth.models import User
    
    usuario_id = request.POST.get('usuario')
    rol_id = request.POST.get('rol')
    
    if not usuario_id or not rol_id:
        messages.error(request, "Debe seleccionar usuario y rol.")
        return redirect('administracion:roles_list')
    
    try:
        usuario = User.objects.get(id=usuario_id)
        rol = Rol.objects.get(id=rol_id)
        
        # Verificar si ya existe la asignación
        if UsuarioRol.objects.filter(usuario=usuario, rol=rol).exists():
            messages.warning(request, f"El usuario {usuario.username} ya tiene el rol {rol.nombre}.")
        else:
            UsuarioRol.objects.create(usuario=usuario, rol=rol)
            messages.success(request, f"Rol {rol.nombre} asignado a {usuario.username}.")
            
    except (User.DoesNotExist, Rol.DoesNotExist):
        messages.error(request, "Usuario o rol no encontrado.")
    
    return redirect('administracion:roles_list')


@requiere_staff_y_permiso('roles', 'revocar')
@require_POST
def revocar_rol(request, asignacion_id):
    """Revoca un rol de un usuario"""
    try:
        asignacion = UsuarioRol.objects.get(id=asignacion_id)
        usuario = asignacion.usuario.username
        rol = asignacion.rol.nombre
        asignacion.delete()
        messages.success(request, f"Rol {rol} revocado de {usuario}.")
    except UsuarioRol.DoesNotExist:
        messages.error(request, "Asignación no encontrada.")
    
    return redirect('administracion:roles_list')


@requiere_staff_y_permiso('roles', 'crear')
def roles_create(request):
    """Crear un nuevo rol"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        permisos_ids = request.POST.getlist('permisos')
        
        if not nombre:
            messages.error(request, "El nombre del rol es obligatorio.")
            return redirect('administracion:roles_create')
        
        # Verificar que no exista un rol con el mismo nombre
        if Rol.objects.filter(nombre=nombre).exists():
            messages.error(request, f"Ya existe un rol con el nombre '{nombre}'.")
            return redirect('administracion:roles_create')
        
        try:
            # Crear el rol
            rol = Rol.objects.create(
                nombre=nombre,
                descripcion=descripcion
            )
            
            # Asignar permisos
            for permiso_id in permisos_ids:
                try:
                    permiso = Permiso.objects.get(id=permiso_id)
                    RolPermiso.objects.create(rol=rol, permiso=permiso)
                except Permiso.DoesNotExist:
                    continue
            
            messages.success(request, f"Rol '{nombre}' creado exitosamente.")
            return redirect('administracion:roles_list')
            
        except Exception as e:
            messages.error(request, f"Error al crear el rol: {str(e)}")
    
    # GET request - mostrar formulario
    permisos = Permiso.objects.all().order_by('modulo', 'accion')
    permisos_por_modulo = {}
    
    for permiso in permisos:
        if permiso.modulo not in permisos_por_modulo:
            permisos_por_modulo[permiso.modulo] = []
        permisos_por_modulo[permiso.modulo].append(permiso)
    
    context = {
        'permisos_por_modulo': permisos_por_modulo,
    }
    
    return render(request, 'administracion/roles_create.html', context)


@requiere_staff_y_permiso('roles', 'editar')
def roles_edit(request, pk):
    """Editar un rol existente"""
    try:
        rol = Rol.objects.get(pk=pk)
    except Rol.DoesNotExist:
        messages.error(request, "El rol no existe.")
        return redirect('administracion:roles_list')
    
    # Verificar que el rol esté activo
    if not rol.activo:
        messages.error(request, "No se pueden editar roles inactivos.")
        return redirect('administracion:roles_list')
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        permisos_ids = request.POST.getlist('permisos')
        
        if not nombre:
            messages.error(request, "El nombre del rol es obligatorio.")
            return redirect('administracion:roles_edit', pk=pk)
        
        # Verificar que no exista otro rol con el mismo nombre
        if Rol.objects.filter(nombre=nombre).exclude(pk=pk).exists():
            messages.error(request, f"Ya existe otro rol con el nombre '{nombre}'.")
            return redirect('administracion:roles_edit', pk=pk)
        
        try:
            # Actualizar el rol
            rol.nombre = nombre
            rol.descripcion = descripcion
            rol.save()
            
            # Eliminar permisos actuales y asignar los nuevos
            RolPermiso.objects.filter(rol=rol).delete()
            for permiso_id in permisos_ids:
                try:
                    permiso = Permiso.objects.get(id=permiso_id)
                    RolPermiso.objects.create(rol=rol, permiso=permiso)
                except Permiso.DoesNotExist:
                    continue
            
            messages.success(request, f"Rol '{nombre}' actualizado exitosamente.")
            return redirect('administracion:roles_list')
            
        except Exception as e:
            messages.error(request, f"Error al actualizar el rol: {str(e)}")
    
    # GET request - mostrar formulario con datos actuales
    permisos = Permiso.objects.all().order_by('modulo', 'accion')
    permisos_por_modulo = {}
    permisos_asignados = set(rol.permisos.values_list('id', flat=True))
    
    for permiso in permisos:
        if permiso.modulo not in permisos_por_modulo:
            permisos_por_modulo[permiso.modulo] = []
        permisos_por_modulo[permiso.modulo].append(permiso)
    
    context = {
        'rol': rol,
        'permisos_por_modulo': permisos_por_modulo,
        'permisos_asignados': permisos_asignados,
    }
    
    return render(request, 'administracion/roles_edit.html', context)


@requiere_staff_y_permiso('roles', 'eliminar')
def roles_delete(request, pk):
    """Eliminar un rol"""
    try:
        rol = Rol.objects.get(pk=pk)
    except Rol.DoesNotExist:
        messages.error(request, "El rol no existe.")
        return redirect('administracion:roles_list')
    
    # Verificar que el rol esté activo
    if not rol.activo:
        messages.error(request, "No se pueden eliminar roles inactivos.")
        return redirect('administracion:roles_list')
    
    # Verificar si hay usuarios asignados a este rol
    usuarios_asignados = UsuarioRol.objects.filter(rol=rol, activo=True).count()
    if usuarios_asignados > 0:
        messages.error(request, f"No se puede eliminar el rol '{rol.nombre}' porque tiene {usuarios_asignados} usuario(s) asignado(s).")
        return redirect('administracion:roles_list')
    
    if request.method == 'POST':
        try:
            nombre_rol = rol.nombre
            rol.delete()
            messages.success(request, f"Rol '{nombre_rol}' eliminado exitosamente.")
            return redirect('administracion:roles_list')
        except Exception as e:
            messages.error(request, f"Error al eliminar el rol: {str(e)}")
    
    context = {
        'rol': rol,
    }
    
    return render(request, 'administracion/roles_confirm_delete.html', context)


# ===== VISTAS DE GESTIÓN DE BLOQUEO DE USUARIOS =====

@requiere_staff_y_permiso('usuarios', 'editar')
@require_POST
def block_user(request, user_id):
    """Vista para bloquear un usuario"""
    usuario = get_object_or_404(User, id=user_id)
    
    # Verificar que no se esté intentando bloquear a un superusuario
    if usuario.is_superuser:
        messages.error(request, "No se puede bloquear a un superusuario.")
        return redirect('administracion:usuario_detail', user_id=user_id)
    
    # Verificar que no se esté intentando bloquear a sí mismo
    if usuario == request.user:
        messages.error(request, "No puedes bloquearte a ti mismo.")
        return redirect('administracion:usuario_detail', user_id=user_id)
    
    # Verificar si el usuario ya está bloqueado
    if usuario.profile.is_blocked:
        messages.warning(request, f"El usuario {usuario.get_full_name() or usuario.username} ya está bloqueado.")
        return redirect('administracion:usuario_detail', user_id=user_id)
    
    try:
        # Obtener el motivo del bloqueo del formulario
        block_reason = request.POST.get('block_reason', '').strip()
        
        # Bloquear al usuario
        usuario.profile.block_user(
            blocked_by=request.user,
            reason=block_reason if block_reason else None
        )
        
        # Mensaje de éxito
        messages.success(
            request, 
            f"Usuario {usuario.get_full_name() or usuario.username} bloqueado exitosamente."
        )
        
        # Log de la acción (opcional)
        print(f"Usuario {usuario.username} bloqueado por {request.user.username} - Motivo: {block_reason or 'Sin motivo especificado'}")
        
    except Exception as e:
        messages.error(request, f"Error al bloquear el usuario: {str(e)}")
    
    return redirect('administracion:usuario_detail', user_id=user_id)


@requiere_staff_y_permiso('usuarios', 'editar')
@require_POST
def unblock_user(request, user_id):
    """Vista para desbloquear un usuario"""
    usuario = get_object_or_404(User, id=user_id)
    
    # Verificar si el usuario no está bloqueado
    if not usuario.profile.is_blocked:
        messages.warning(request, f"El usuario {usuario.get_full_name() or usuario.username} no está bloqueado.")
        return redirect('administracion:usuario_detail', user_id=user_id)
    
    try:
        # Desbloquear al usuario
        usuario.profile.unblock_user()
        
        # Mensaje de éxito
        messages.success(
            request, 
            f"Usuario {usuario.get_full_name() or usuario.username} desbloqueado exitosamente."
        )
        
        # Log de la acción (opcional)
        print(f"Usuario {usuario.username} desbloqueado por {request.user.username}")
        
    except Exception as e:
        messages.error(request, f"Error al desbloquear el usuario: {str(e)}")
    
    return redirect('administracion:usuario_detail', user_id=user_id)
