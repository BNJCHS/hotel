import os
import json
from datetime import datetime

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpRequest
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

from habitaciones.models import Habitacion
from reservas.models import Reserva

# OpenAI client (new SDK)
from openai import OpenAI

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

FAQ = [
    {"q": "¿Cuáles son los horarios de check-in y check-out?", "a": "Check-in desde las 14:00 y check-out hasta las 11:00."},
    {"q": "¿Aceptan mascotas?", "a": "Sí, aceptamos mascotas pequeñas con un cargo adicional."},
    {"q": "¿Incluye desayuno?", "a": "Dependiendo del plan, algunas tarifas incluyen desayuno buffet."},
]


def parse_dates(text):
    try:
        # Espera formato YYYY-MM-DD
        date_obj = datetime.strptime(text, "%Y-%m-%d").date()
        return date_obj
    except Exception:
        return None


def find_available_room(room_type: str):
    if not room_type:
        return None
    room_type = room_type.lower()
    return Habitacion.objects.filter(tipo__iexact=room_type, disponible=True).first()


@csrf_exempt
def chat_endpoint(request: HttpRequest):
    if request.method != 'POST':
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido"}, status=400)

    user_message = payload.get('message', '').strip()
    user_id = payload.get('user_id')  # opcional

    if not user_message:
        return JsonResponse({"error": "Mensaje vacío"}, status=400)

    # Contexto para el modelo
    system_prompt = (
        "Eres el asistente del Hotel Elegante. Respondes preguntas frecuentes breves y claras. "
        "Cuando el usuario exprese intención de reservar, extrae: nombre, tipo_habitacion (simple/doble/suite), "
        "check_in (YYYY-MM-DD), check_out (YYYY-MM-DD) y cantidad_huespedes. Responde en JSON bajo la clave 'reservation' "
        "si está toda la info, de lo contrario sigue conversando."
    )

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,
        )
        ai_text = completion.choices[0].message.content
    except Exception as e:
        return JsonResponse({"error": "Error llamando a OpenAI", "details": str(e)}, status=500)

    # Intentar interpretar JSON de reserva
    reservation_data = None
    try:
        parsed = json.loads(ai_text)
        reservation_data = parsed.get('reservation')
    except Exception:
        reservation_data = None

    # Si hay datos de reserva completos, validar y crear
    if reservation_data:
        nombre = reservation_data.get('nombre')
        tipo_habitacion = reservation_data.get('tipo_habitacion')
        check_in = parse_dates(reservation_data.get('check_in', ''))
        check_out = parse_dates(reservation_data.get('check_out', ''))
        cantidad = reservation_data.get('cantidad_huespedes') or 1

        if not (tipo_habitacion and check_in and check_out and check_in < check_out):
            return JsonResponse({
                "message": "Necesito confirmar datos: tipo de habitación y fechas válidas (YYYY-MM-DD).",
                "need_confirmation": True
            })

        room = find_available_room(tipo_habitacion)
        if not room:
            return JsonResponse({
                "message": f"No hay disponibilidad para habitación {tipo_habitacion}. ¿Quieres otra fecha o tipo?",
                "need_confirmation": True
            })

        # Resolver usuario: si está autenticado úsalo, si no, crear/usar invitado
        if request.user.is_authenticated:
            user = request.user
        else:
            # fallback: crear usuario temporal por nombre
            if not nombre:
                return JsonResponse({
                    "message": "¿A nombre de quién hacemos la reserva?",
                    "need_confirmation": True
                })
            username = f"guest_{nombre.lower().replace(' ', '_')}"
            user, _ = User.objects.get_or_create(username=username, defaults={"first_name": nombre})

        # Crear reserva
        reserva = Reserva.objects.create(
            usuario=user,
            habitacion=room,
            check_in=check_in,
            check_out=check_out,
            cantidad_huespedes=cantidad,
            confirmada=True,
            activada=False,
        )

        message = (
            f"Reserva creada: Habitación {room.numero} ({room.tipo}) del {check_in} al {check_out} para {cantidad} huésped(es). "
            f"Código: {reserva.token}."
        )
        return JsonResponse({
            "message": message,
            "reservation_id": reserva.id,
            "token": reserva.token,
            "created": True
        })

    # Si no es reserva, responder FAQ o devolver respuesta genérica del modelo
    # Buscar respuesta simple en FAQ
    for item in FAQ:
        if item["q"].lower() in user_message.lower():
            return JsonResponse({"message": item["a"], "created": False})

    # Fallback: devolver texto del modelo
    return JsonResponse({"message": ai_text, "created": False})