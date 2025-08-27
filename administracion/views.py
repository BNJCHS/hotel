from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q
from reservas.models import Reserva
from .models import Empleado, Plan, Promocion, Servicio, Huesped
from .forms import EmpleadoForm, PlanForm, PromocionForm, ServicioForm, HuespedForm
from reservas.models import Huesped 

from django.db.models import Sum

def dashboard(request):
    total_reservas = Reserva.objects.count()
    total_ingresos = Reserva.objects.aggregate(total=Sum("monto"))["total"] or 0
    total_huespedes = Huesped.objects.count()
    total_empleados = Empleado.objects.count()

    reservas = Reserva.objects.order_by("-fecha_reserva")[:5]  # últimas 5

    context = {
        "total_reservas": total_reservas,
        "total_ingresos": total_ingresos,
        'total_huespedes': total_huespedes,
        "total_empleados": total_empleados,
        "reservas": reservas,
    }
    return render(request, "administracion/dashboard.html", context)

# ===== Helpers =====
def _paginate(request, queryset, per_page=10):
    page_number = request.GET.get("page")
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(page_number)

# ===================== EMPLEADOS =====================
def empleados_list(request):
    q = request.GET.get("q", "")
    qs = Empleado.objects.all()
    if q:
        qs = qs.filter(
            Q(nombre__icontains=q) | Q(apellido__icontains=q) | Q(dni__icontains=q) | Q(puesto__icontains=q)
        )
    page_obj = _paginate(request, qs, 10)
    return render(request, "administracion/empleados_list.html", {"page_obj": page_obj, "q": q})

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

def empleados_delete(request, pk):
    obj = get_object_or_404(Empleado, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Empleado eliminado.")
        return redirect("empleados_list")
    return render(request, "administracion/empleados_confirm_delete.html", {"empleado": obj})

# ===================== PLANES =====================
def planes_list(request):
    q = request.GET.get("q", "")
    qs = Plan.objects.all()
    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(descripcion__icontains=q))
    page_obj = _paginate(request, qs, 10)
    return render(request, "administracion/planes_list.html", {"page_obj": page_obj, "q": q})

def planes_create(request):
    if request.method == "POST":
        form = PlanForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Plan creado correctamente.")
            return redirect("planes_list")
    else:
        form = PlanForm()
    return render(request, "administracion/planes_form.html", {"form": form})

def planes_edit(request, pk):
    obj = get_object_or_404(Plan, pk=pk)
    if request.method == "POST":
        form = PlanForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Plan actualizado.")
            return redirect("planes_list")
    else:
        form = PlanForm(instance=obj)
    return render(request, "administracion/planes_form.html", {"form": form})

def planes_delete(request, pk):
    obj = get_object_or_404(Plan, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Plan eliminado.")
        return redirect("planes_list")
    return render(request, "administracion/planes_confirm_delete.html", {"plan": obj})

# ===================== PROMOCIONES =====================
def promociones_list(request):
    q = request.GET.get("q", "")
    qs = Promocion.objects.all()
    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(descripcion__icontains=q))
    page_obj = _paginate(request, qs, 10)
    return render(request, "administracion/promociones_list.html", {"page_obj": page_obj, "q": q})

def promociones_create(request):
    if request.method == "POST":
        form = PromocionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Promoción creada correctamente.")
            return redirect("promociones_list")
    else:
        form = PromocionForm()
    return render(request, "administracion/promociones_form.html", {"form": form})

def promociones_edit(request, pk):
    obj = get_object_or_404(Promocion, pk=pk)
    if request.method == "POST":
        form = PromocionForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Promoción actualizada.")
            return redirect("promociones_list")
    else:
        form = PromocionForm(instance=obj)
    return render(request, "administracion/promociones_form.html", {"form": form})

def promociones_delete(request, pk):
    obj = get_object_or_404(Promocion, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Promoción eliminada.")
        return redirect("promociones_list")
    return render(request, "administracion/promociones_confirm_delete.html", {"promocion": obj})

# ===================== SERVICIOS =====================
def servicios_list(request):
    q = request.GET.get("q", "")
    qs = Servicio.objects.all()
    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(descripcion__icontains=q))
    page_obj = _paginate(request, qs, 10)
    return render(request, "administracion/servicios_list.html", {"page_obj": page_obj, "q": q})

def servicios_create(request):
    if request.method == "POST":
        form = ServicioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Servicio creado correctamente.")
            return redirect("servicios_list")
    else:
        form = ServicioForm()
    return render(request, "administracion/servicios_form.html", {"form": form})

def servicios_edit(request, pk):
    obj = get_object_or_404(Servicio, pk=pk)
    if request.method == "POST":
        form = ServicioForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Servicio actualizado.")
            return redirect("servicios_list")
    else:
        form = ServicioForm(instance=obj)
    return render(request, "administracion/servicios_form.html", {"form": form})

def servicios_delete(request, pk):
    obj = get_object_or_404(Servicio, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Servicio eliminado.")
        return redirect("servicios_list")
    return render(request, "administracion/servicios_confirm_delete.html", {"servicio": obj})

# ===================== HUÉSPEDES =====================
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

def huespedes_delete(request, pk):
    obj = get_object_or_404(Huesped, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Huésped eliminado.")
        return redirect("huespedes_list")
    return render(request, "administracion/huespedes_confirm_delete.html", {"huesped": obj})
