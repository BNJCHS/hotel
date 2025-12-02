from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q, Sum
from django.utils import timezone
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.urls import reverse
from reservas.models import Reserva
from .models import Empleado, Plan, Promocion, Servicio, Huesped, Rol, UsuarioRol, Permiso, RolPermiso
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

# imports para envío de emails
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.http import HttpResponse

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
    from reservas.models import HuespedActivo
    reserva = get_object_or_404(Reserva, id=reserva_id)
    hoy = timezone.now().date()

    # Validaciones de estado y fecha
    if reserva.estado != 'confirmada':
        messages.error(request, 'Sólo se puede activar una reserva confirmada.')
        return redirect('administracion:ver_reservas')

    if not reserva.check_in:
        messages.error(request, 'La reserva no tiene fecha de check-in definida.')
        return redirect('administracion:ver_reservas')

    if reserva.check_in != hoy:
        messages.error(request, 'La reserva sólo puede activarse el primer día de check-in.')
        return redirect('administracion:ver_reservas')

    # Evitar activar si ya está activa
    if reserva.estado == 'activa':
        messages.info(request, 'La reserva ya está activa.')
        return redirect('administracion:ver_reservas')

    # Validar código de check-in
    codigo_checkin_form = request.POST.get('codigo_checkin', '').strip()
    if not codigo_checkin_form or codigo_checkin_form != reserva.codigo_checkin:
        messages.error(request, 'El código de check-in es incorrecto.')
        return redirect('administracion:ver_reservas')

    # Activar estado y (opcionalmente) mantener la habitación asignada si ya existe
    reserva.activar()

    # Crear huéspedes activos para cada huésped de la reserva
    creados = 0
    for h in reserva.huespedes.all():
        obj, creado = HuespedActivo.objects.get_or_create(
            huesped=h,
            reserva=reserva,
            defaults={
                'habitacion': reserva.habitacion_asignada,
                'fecha_checkin': hoy,
                'fecha_checkout': reserva.check_out,
                'activo': True,
            }
        )
        if creado:
            creados += 1

    messages.success(request, f"Reserva activada. Huéspedes activos creados: {creados}.")
    return redirect('administracion:ver_reservas')

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
@require_POST
def planes_send_email(request, pk):
    """Envía el plan por email a usuarios con notificaciones activadas en el admin personalizado (HTML + CTA)."""
    plan = get_object_or_404(Plan, pk=pk)

    users = User.objects.filter(is_active=True).exclude(email="").select_related('profile')
    recipients = []
    excluidos = 0
    for u in users:
        try:
            prefs = getattr(u.profile, 'preferences', {}) or {}
            if prefs.get('notifications_enabled', True):
                recipients.append(u.email)
            else:
                excluidos += 1
        except Exception:
            recipients.append(u.email)
    recipients = list(dict.fromkeys(recipients))

    if not recipients:
        messages.warning(request, 'No hay usuarios con notificaciones activadas o emails válidos.')
        return redirect('administracion:planes_list')

    today = timezone.now().date()
    plan_url = request.build_absolute_uri(reverse('detalle_plan', args=[plan.id]))
    imagen_url = request.build_absolute_uri(plan.imagen.url) if getattr(plan, 'imagen', None) else None

    subject = f"Plan: {plan.nombre}"

    html_body = render_to_string('emails/plan_email.html', {
        'plan': plan,
        'plan_url': plan_url,
        'imagen_url': imagen_url,
        'year': today.year,
    })
    text_body = strip_tags(html_body)

    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
            bcc=recipients,
        )
        email.attach_alternative(html_body, "text/html")
        email.send(fail_silently=False)
        messages.success(request, f'Plan "{plan.nombre}" enviado por email a {len(recipients)} usuarios. Excluidos por preferencia: {excluidos}.')
    except Exception as e:
        messages.error(request, f'Error al enviar "{plan.nombre}": {e}')

    return redirect('administracion:planes_list')

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

@requiere_staff_y_permiso('promociones', 'editar')
@require_POST
def promociones_send_email(request, pk):
    """Envía la promoción por email a usuarios con notificaciones activadas en el admin personalizado (HTML + CTA)."""
    promo = get_object_or_404(Promocion, pk=pk)

    users = User.objects.filter(is_active=True).exclude(email="").select_related('profile')
    recipients = []
    excluidos = 0
    for u in users:
        try:
            prefs = getattr(u.profile, 'preferences', {}) or {}
            if prefs.get('notifications_enabled', True):
                recipients.append(u.email)
            else:
                excluidos += 1
        except Exception:
            recipients.append(u.email)
    recipients = list(dict.fromkeys(recipients))

    if not recipients:
        messages.warning(request, 'No hay usuarios con notificaciones activadas o emails válidos.')
        return redirect('administracion:promociones_list')

    today = timezone.now().date()
    is_active = promo.fecha_inicio <= today <= promo.fecha_fin
    estado = 'activa' if is_active else ('proxima' if today < promo.fecha_inicio else 'finalizada')
    dias_restantes = (promo.fecha_fin - today).days if is_active else 0
    dias_para_inicio = (promo.fecha_inicio - today).days if today < promo.fecha_inicio else 0

    promo_url = request.build_absolute_uri(reverse('promocion_detalle', args=[promo.id]))
    imagen_url = request.build_absolute_uri(promo.imagen.url) if getattr(promo, 'imagen', None) else None

    subject = f"Promoción: {promo.nombre} ({promo.descuento}%)"

    html_body = render_to_string('emails/promocion_email.html', {
        'promocion': promo,
        'estado': estado,
        'dias_restantes': dias_restantes,
        'dias_para_inicio': dias_para_inicio,
        'promo_url': promo_url,
        'imagen_url': imagen_url,
        'year': today.year,
    })
    text_body = strip_tags(html_body)

    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
            bcc=recipients,
        )
        email.attach_alternative(html_body, "text/html")
        email.send(fail_silently=False)
        messages.success(request, f'Promoción "{promo.nombre}" enviada por email a {len(recipients)} usuarios. Excluidos por preferencia: {excluidos}.')
    except Exception as e:
        messages.error(request, f'Error al enviar "{promo.nombre}": {e}')

    return redirect('administracion:promociones_list')

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

@requiere_staff_y_permiso('huespedes', 'ver')
def huesped_detail(request, pk):
    """Detalle de huésped del módulo administración, con reservas asociadas por DNI."""
    obj = get_object_or_404(Huesped, pk=pk)
    reservas_del_huesped = []
    if obj.dni:
        reservas_del_huesped = ReservaHuesped.objects.filter(dni=obj.dni).select_related('reserva')
    # también buscar por nombre+apellido si no hay DNI
    elif obj.nombre and obj.apellido:
        reservas_del_huesped = ReservaHuesped.objects.filter(nombre=obj.nombre, apellido=obj.apellido).select_related('reserva')
    return render(request, 'administracion/huesped_detail.html', {
        'huesped': obj,
        'reservas_huesped': reservas_del_huesped,
    })

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
    reservas_qs = Reserva.objects.select_related('usuario', 'tipo_habitacion', 'habitacion_asignada', 'plan', 'promocion') \
                                 .prefetch_related('servicios') \
                                 .order_by('-fecha_reserva')

    # Buscar por ID de reserva (GET param 'id' o 'q')
    query_id = (request.GET.get('id') or request.GET.get('q') or '').strip()
    if query_id:
        try:
            id_num = int(query_id)
            reservas_qs = reservas_qs.filter(id=id_num)
        except ValueError:
            messages.error(request, 'El ID debe ser un número entero.')

    hoy = timezone.now().date()
    return render(request, 'administracion/ver_reservas.html', {
        'reservas': reservas_qs,
        'hoy': hoy,
        'query_id': query_id,
    })

@requiere_staff_y_permiso('reservas', 'confirmar')
@require_POST
def confirmar_reserva_admin(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    if reserva.estado == 'confirmada':
        messages.info(request, "La reserva ya está confirmada.")
        return redirect('administracion:ver_reservas')

    reserva.estado = 'confirmada'
    reserva.save()

    # Reservar las habitaciones del tipo solicitado
    tipo_habitacion = reserva.tipo_habitacion
    tipo_habitacion.reservar_stock(reserva.cantidad_habitaciones)

    messages.success(request, f"Reserva confirmada.")
    return redirect('administracion:ver_reservas')

@requiere_staff_y_permiso('reservas', 'confirmar')
@require_POST
def finalizar_reserva_admin(request, reserva_id):
    """Finaliza (checkout) una reserva activa sólo en su último día.
    Desactiva todos los HuespedActivo asociados y completa la reserva."""
    from reservas.models import HuespedActivo

    reserva = get_object_or_404(Reserva, id=reserva_id)
    hoy = timezone.now().date()

    if reserva.estado != 'activa':
        messages.error(request, 'Sólo se puede finalizar una reserva activa.')
        return redirect('administracion:ver_reservas')

    if not reserva.check_out:
        messages.error(request, 'La reserva no tiene fecha de check-out definida.')
        return redirect('administracion:ver_reservas')

    if reserva.check_out != hoy:
        messages.error(request, 'El checkout sólo se puede realizar el último día de la reserva.')
        return redirect('administracion:ver_reservas')

    # Finalizar huéspedes activos vinculados
    activos = HuespedActivo.objects.filter(reserva=reserva, activo=True)
    count = 0
    for ha in activos:
        ha.finalizar(fecha=hoy)
        count += 1

    # Marcar habitación disponible si no quedan activos
    habit = reserva.habitacion_asignada
    if habit:
        otras = HuespedActivo.objects.filter(habitacion=habit, activo=True).exists()
        if not otras and hasattr(habit, 'disponible'):
            habit.disponible = True
            habit.save()

    # Completar la reserva (libera stock)
    reserva.completar()
    messages.success(request, f'Reserva finalizada. Huéspedes desactivados: {count}.')
    return redirect('administracion:ver_reservas')

@requiere_staff_y_permiso('reservas', 'confirmar')
@require_POST
def activar_reserva(request, reserva_id):
    from reservas.models import HuespedActivo
    reserva = get_object_or_404(Reserva, id=reserva_id)
    hoy = timezone.now().date()

    # Validaciones de estado y fecha
    if reserva.estado != 'confirmada':
        messages.error(request, 'Sólo se puede activar una reserva confirmada.')
        return redirect('administracion:ver_reservas')

    if not reserva.check_in:
        messages.error(request, 'La reserva no tiene fecha de check-in definida.')
        return redirect('administracion:ver_reservas')

    if reserva.check_in != hoy:
        messages.error(request, 'La reserva sólo puede activarse el primer día de check-in.')
        return redirect('administracion:ver_reservas')

    # Evitar activar si ya está activa
    if reserva.estado == 'activa':
        messages.info(request, 'La reserva ya está activa.')
        return redirect('administracion:ver_reservas')

    # Validar código de check-in
    codigo_checkin_form = request.POST.get('codigo_checkin', '').strip()
    if not codigo_checkin_form or codigo_checkin_form != reserva.codigo_checkin:
        messages.error(request, 'El código de check-in es incorrecto.')
        return redirect('administracion:ver_reservas')

    # Activar estado y (opcionalmente) mantener la habitación asignada si ya existe
    reserva.activar()

    # Crear huéspedes activos para cada huésped de la reserva
    creados = 0
    for h in reserva.huespedes.all():
        obj, creado = HuespedActivo.objects.get_or_create(
            huesped=h,
            reserva=reserva,
            defaults={
                'habitacion': reserva.habitacion_asignada,
                'fecha_checkin': hoy,
                'fecha_checkout': reserva.check_out,
                'activo': True,
            }
        )
        if creado:
            creados += 1

    messages.success(request, f"Reserva activada. Huéspedes activos creados: {creados}.")
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
    return redirect('administracion:ver_reservas')


@requiere_staff_y_permiso('huespedes', 'ver')
def huespedes_activos(request):
    from reservas.models import HuespedActivo
    hoy = timezone.now().date()
    activos_qs = HuespedActivo.objects.filter(
        activo=True
    ).filter(
        Q(fecha_checkin__lte=hoy) | Q(fecha_checkin__isnull=True),
        Q(fecha_checkout__gte=hoy) | Q(fecha_checkout__isnull=True)
    ).select_related('huesped', 'reserva', 'habitacion')

    # Filtro por ID de reserva (GET ?reserva=<id>)
    reserva_id = request.GET.get('reserva')
    if reserva_id:
        try:
            reserva_id_int = int(reserva_id)
            activos_qs = activos_qs.filter(reserva_id=reserva_id_int)
        except ValueError:
            messages.error(request, 'ID de reserva inválido.')

    return render(request, 'administracion/huespedes_activos.html', {
        'activos': activos_qs,
        'reserva_id': reserva_id or '',
    })


@requiere_staff_y_permiso('huespedes', 'editar')
@require_POST
def finalizar_huesped_activo(request, activo_id):
    from reservas.models import HuespedActivo
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
    return redirect('administracion:huespedes_activos')


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


@requiere_staff_y_permiso('promociones', 'ver')
def promociones_preview_email(request, pk):
    """Previsualiza el email HTML de una promoción en el navegador."""
    promo = get_object_or_404(Promocion, pk=pk)
    today = timezone.now().date()
    is_active = promo.fecha_inicio <= today <= promo.fecha_fin
    estado = 'activa' if is_active else ('proxima' if today < promo.fecha_inicio else 'finalizada')
    dias_restantes = (promo.fecha_fin - today).days if is_active else 0
    dias_para_inicio = (promo.fecha_inicio - today).days if today < promo.fecha_inicio else 0

    promo_url = request.build_absolute_uri(reverse('promocion_detalle', args=[promo.id]))
    imagen_url = request.build_absolute_uri(promo.imagen.url) if getattr(promo, 'imagen', None) else None

    html = render_to_string('emails/promocion_email.html', {
        'promocion': promo,
        'estado': estado,
        'dias_restantes': dias_restantes,
        'dias_para_inicio': dias_para_inicio,
        'promo_url': promo_url,
        'imagen_url': imagen_url,
        'year': today.year,
    })
    return HttpResponse(html)

@requiere_staff_y_permiso('planes', 'ver')
def planes_preview_email(request, pk):
    """Previsualiza el email HTML de un plan en el navegador."""
    plan = get_object_or_404(Plan, pk=pk)
    today = timezone.now().date()

    plan_url = request.build_absolute_uri(reverse('detalle_plan', args=[plan.id]))
    imagen_url = request.build_absolute_uri(plan.imagen.url) if getattr(plan, 'imagen', None) else None

    html = render_to_string('emails/plan_email.html', {
        'plan': plan,
        'plan_url': plan_url,
        'imagen_url': imagen_url,
        'year': today.year,
    })
    return HttpResponse(html)





