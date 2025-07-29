
from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import RegistroForm

def register(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Inicia sesión automáticamente
            return redirect('index.html')  # Cambia por tu URL principal
    else:
        form = RegistroForm()
    return render(request, 'register.html', {'form': form})
