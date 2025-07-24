from django.shortcuts import render

def index(request):
    return render(request, 'administracion/index.html')  # Cambiar "hotel" por el nombre de la app si es necesario
