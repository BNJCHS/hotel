
from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import RegistroForm

def register(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            print("Formulario válido")  # <---
            user = form.save()
            login(request, user)
            return redirect('index')
        else:
            print("Formulario inválido")  # <---
            print(form.errors)  # Muestra errores
    else:
        form = RegistroForm()
    return render(request, 'register.html', {'form': form})

from django.contrib.auth import logout
from django.shortcuts import redirect

def logout_view(request):
    logout(request)
    return redirect('login')  # 👈 redirige a tu login personalizado
