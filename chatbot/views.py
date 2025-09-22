import os
import json
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.utils.dateparse import parse_date
from habitaciones.models import Habitacion
from reservas.models import Reserva

# OpenAI SDK v1.x (import seguro)
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

_client = None

def get_openai_client():
    global _client
    if _client is None and OpenAI is not None:
        _client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    return _client

# -------------------- Utilidades de parsing y estado --------------------

def parse_dates(text):
    """
    Very simple date parser expecting YYYY-MM-DD patterns in text.
    Returns (check_in, check_out) as date objects or (None, None).
    """
    try:
        parts = [p for p in text.split() if '-' in p and len(p) >= 8]
        dates = []
        for p in parts:
            d = parse_date(p.strip('.,;'))
            if d:
                dates.append(d)
        if len(dates) >= 2:
            dates.sort()
            return dates[0], dates[1]
    except Exception:
        pass
    return None, None


def parse_guests(text):
    # Busca el primer número en el texto como cantidad de huéspedes
    import re
    m = re.search(r"(\d+)", text)
    if m:
        try:
            val = int(m.group(1))
            if 1 <= val <= 10:
                return val
        except Exception:
            pass
    # Palabras clave simples
    lower = text.lower()
    if "una" in lower or "uno" in lower:
        return 1
    if "dos" in lower:
        return 2
    if "tres" in lower:
        return 3
    if "cuatro" in lower:
        return 4
    return None


def parse_room_type(text):
    lower = text.lower()
    for t in ["simple", "doble", "suite", "presidencial"]:
        if t in lower:
            return t
    return None

# NUEVO: detectar múltiples tipos en el mismo mensaje
def parse_room_types(text):
    lower = text.lower()
    tipos_validos = ["simple", "doble", "suite", "presidencial"]
    encontrados = []
    for t in tipos_validos:
        if t in lower:
            encontrados.append(t)
    # deduplicar conservando orden
    seen = set()
    result = []
    for t in encontrados:
        if t not in seen:
            result.append(t)
            seen.add(t)
    return result


def parse_room_choice(text):
    """Extrae un número de habitación elegido por el usuario si lo menciona."""
    import re
    m = re.search(r"habitaci[oó]n\s*(\d+)|\b(\d{1,4})\b", text.lower())
    if m:
        num = m.group(1) or m.group(2)
        try:
            return int(num)
        except Exception:
            return None
    return None


def get_state(request):
    return request.session.get('chatbot_state', {
        'stage': 'collecting',
        'data': {
            'tipo': None,
            'tipos': [],  # <- soporta múltiples tipos
            'check_in': None,
            'check_out': None,
            'cantidad_huespedes': None,
            'opciones': [],  # números de habitación sugeridos
            'eleccion': None,
        }
    })


def save_state(request, state):
    request.session['chatbot_state'] = state
    request.session.modified = True


def reset_state(request):
    if 'chatbot_state' in request.session:
        del request.session['chatbot_state']
        request.session.modified = True


# -------------------- OpenAI extracción --------------------

def extract_intent_and_entities(message):
    """Call OpenAI to extract intent and reservation fields from the message. Fallback to simple parsing if unavailable."""
    client = get_openai_client()
    if client is None:
        # Fallback: naive parsing
        ci, co = parse_dates(message)
        # intentar múltiples tipos
        tipos_detectados = parse_room_types(message)
        tipo = tipos_detectados[0] if tipos_detectados else parse_room_type(message)
        cant = parse_guests(message)
        data = {
            "intent": "reservar" if (ci and co and (tipo or cant)) else "consulta",
            "nombre": None,
            "tipo_habitacion": tipo,
            "fechas": {"check_in": ci.isoformat(), "check_out": co.isoformat()} if ci and co else None,
            "cantidad_huespedes": cant,
            "note": "fallback_parser"
        }
        return data

    prompt = f"""
Eres un asistente para un hotel. Analiza el mensaje de usuario y devuelve un JSON compacto con:
- intent: uno de [reservar, consulta, otro]
- nombre: nombre del cliente si lo menciona, si no null
- tipo_habitacion: uno de [simple, doble, suite, presidencial] si lo menciona, si no null
- fechas: objeto con check_in y check_out en formato YYYY-MM-DD si las menciona, si no null
- cantidad_huespedes: entero si lo menciona, si no null

Mensaje: "{message}"
Responde SOLO el JSON sin texto extra.
"""
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un asistente que extrae intención y entidades para reservas de hotel."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        content = completion.choices[0].message.content.strip()
        content = content.replace('```json', '').replace('```', '').strip()
        data = json.loads(content)
        if (not data.get('fechas')):
            ci, co = parse_dates(message)
            if ci and co:
                data['fechas'] = {"check_in": ci.isoformat(), "check_out": co.isoformat()}
        if (not data.get('cantidad_huespedes')):
            cant = parse_guests(message)
            if cant:
                data['cantidad_huespedes'] = cant
        if (not data.get('tipo_habitacion')):
            t = parse_room_type(message)
            if t:
                data['tipo_habitacion'] = t
        return data
    except Exception as e:
        return {"intent": "otro", "error": str(e)}


# -------------------- Disponibilidad por fechas --------------------

# Acepta múltiples tipos

def find_available_rooms_by_dates(tipos=None, capacidad_min=1, check_in=None, check_out=None, limit=3):
    qs = Habitacion.objects.filter(capacidad__gte=capacidad_min)
    if tipos:
        qs = qs.filter(tipo__in=tipos)
    # excluir habitaciones con reservas que se superpongan
    overlapping = {
        'reserva__check_in__lt': check_out,
        'reserva__check_out__gt': check_in,
    }
    qs = qs.exclude(**overlapping)
    # Además, si hay un flag "disponible", respetarlo como disponibilidad general
    qs = qs.filter(disponible=True)
    return list(qs.order_by('precio', 'numero')[:limit])


# -------------------- Vista principal con flujo paso a paso --------------------

@csrf_exempt
@require_POST
def chat(request):
    try:
        body = json.loads(request.body)
        message = body.get('message', '')
        user_id = body.get('user_id')

        if not message:
            return JsonResponse({"success": False, "message": "Mensaje vacío"}, status=400)

        # Cargar/actualizar estado
        state = get_state(request)
        data = state['data']

        # Extraer entidades del mensaje
        extracted = extract_intent_and_entities(message)
        intent = extracted.get('intent', 'otro')

        # Rellenar datos faltantes en el estado con lo que venga del mensaje
        if not data.get('tipo') and extracted.get('tipo_habitacion'):
            data['tipo'] = extracted.get('tipo_habitacion')
        # Asegurar lista de tipos a partir del mensaje y de lo extraído
        tipos_msg = parse_room_types(message)
        for t in tipos_msg:
            if t not in data.get('tipos', []):
                data.setdefault('tipos', []).append(t)
        if extracted.get('tipo_habitacion'):
            t = extracted['tipo_habitacion']
            if t and t not in data.get('tipos', []):
                data.setdefault('tipos', []).append(t)

        if not (data.get('check_in') and data.get('check_out')) and extracted.get('fechas'):
            f = extracted['fechas']
            data['check_in'] = f.get('check_in')
            data['check_out'] = f.get('check_out')
        if not data.get('cantidad_huespedes') and extracted.get('cantidad_huespedes'):
            data['cantidad_huespedes'] = extracted.get('cantidad_huespedes')

        # Parsing adicional por si el usuario responde a una pregunta
        ci, co = parse_dates(message)
        if ci and co:
            data['check_in'] = ci.isoformat()
            data['check_out'] = co.isoformat()
        # compat: si el usuario dijo un único tipo explícito en una respuesta breve
        tipo_msg = parse_room_type(message)
        if tipo_msg and tipo_msg not in data.get('tipos', []):
            data.setdefault('tipos', []).append(tipo_msg)
            if not data.get('tipo'):
                data['tipo'] = tipo_msg
        cant_msg = parse_guests(message)
        if cant_msg:
            data['cantidad_huespedes'] = cant_msg

        # Si el usuario elige una habitación explícitamente
        choice = parse_room_choice(message)
        if choice:
            data['eleccion'] = choice

        # Determinar siguiente paso según estado y datos
        missing = []
        if not data.get('check_in') or not data.get('check_out'):
            missing.append('fechas (check-in y check-out)')
        # Requerir al menos un tipo (soportando múltiples)
        if not data.get('tipos') and not data.get('tipo'):
            missing.append('tipo(s) de habitación (simple, doble, suite, presidencial)')
        if not data.get('cantidad_huespedes'):
            missing.append('cantidad de huéspedes')

        # Paso 1: recopilar datos necesarios
        if missing:
            save_state(request, state)
            return JsonResponse({
                "success": True,
                "stage": "collecting",
                "message": "Para avanzar necesito: " + ", ".join(missing) + ".",
                "entities": extracted,
                "data": data,
            })

        # Parsear fechas a objeto date
        check_in = parse_date(data['check_in']) if isinstance(data['check_in'], str) else data['check_in']
        check_out = parse_date(data['check_out']) if isinstance(data['check_out'], str) else data['check_out']
        if not check_in or not check_out or check_in >= check_out:
            save_state(request, state)
            return JsonResponse({
                "success": True,
                "stage": "collecting",
                "message": "Las fechas no son válidas. Por favor, envíame check-in y check-out en formato YYYY-MM-DD (ej: 2025-10-01 2025-10-05).",
                "data": data,
            })

        # Paso 2: verificar disponibilidad y proponer opciones
        if state['stage'] in ['collecting', 'options']:
            tipos_busqueda = data.get('tipos') or ([data['tipo']] if data.get('tipo') else None)
            rooms = find_available_rooms_by_dates(
                tipos=tipos_busqueda,
                capacidad_min=int(data['cantidad_huespedes']),
                check_in=check_in,
                check_out=check_out,
                limit=3
            )
            if not rooms:
                save_state(request, state)
                return JsonResponse({
                    "success": True,
                    "stage": "options",
                    "message": "No hay disponibilidad con esos criterios. Puedes ampliar los tipos (simple, doble, suite, presidencial) o cambiar fechas/huéspedes. ¿Qué deseas ajustar?",
                    "data": data,
                })
            data['opciones'] = [r.numero for r in rooms]
            state['stage'] = 'confirm'
            save_state(request, state)
            return JsonResponse({
                "success": True,
                "stage": "confirm",
                "message": "Tengo estas opciones disponibles: " + ", ".join([f"Habitación {n}" for n in data['opciones']]) + ". Dime el número de habitación para continuar o escribe 'otra' para cambiar criterios.",
                "options": data['opciones'],
                "data": data,
            })

        # Paso 3: confirmación de la reserva con elección
        if state['stage'] == 'confirm':
            # Si el usuario pide cambiar
            if 'otra' in message.lower() or 'cambiar' in message.lower():
                state['stage'] = 'collecting'
                data['opciones'] = []
                data['eleccion'] = None
                save_state(request, state)
                return JsonResponse({
                    "success": True,
                    "stage": "collecting",
                    "message": "Perfecto, dime qué criterio deseas cambiar (fechas, tipo(s), huéspedes). Puedes indicar varios tipos a la vez (ej: doble y suite).",
                    "data": data,
                })

            # Si elige una habitación de la lista
            if (data.get('eleccion') in data.get('opciones', [])):
                # Confirmar creación
                # Determinar usuario
                user = None
                if user_id:
                    user = User.objects.filter(id=user_id).first()
                if not user:
                    user, _ = User.objects.get_or_create(username='chatbot_user', defaults={"first_name": "Invitado"})

                room = Habitacion.objects.filter(numero=data['eleccion']).first()
                if not room:
                    # Actualizar opciones otra vez
                    state['stage'] = 'collecting'
                    save_state(request, state)
                    return JsonResponse({
                        "success": True,
                        "stage": "collecting",
                        "message": "Esa opción ya no está disponible. Volvamos a intentar con otros criterios.",
                    })

                reserva = Reserva.objects.create(
                    usuario=user,
                    habitacion=room,
                    check_in=check_in,
                    check_out=check_out,
                    cantidad_huespedes=int(data['cantidad_huespedes']),
                    confirmada=True,
                )

                # No cambiar room.disponible aquí; usamos disponibilidad por fechas.

                # Resetear estado tras crear
                reset_state(request)

                return JsonResponse({
                    "success": True,
                    "stage": "done",
                    "message": f"Reserva confirmada para la habitación {room.numero} ({room.tipo}) del {check_in} al {check_out}.",
                    "reserva": {
                        "id": reserva.id,
                        "habitacion": room.numero,
                        "tipo": room.tipo,
                        "check_in": reserva.check_in.isoformat() if reserva.check_in else None,
                        "check_out": reserva.check_out.isoformat() if reserva.check_out else None,
                        "cantidad_huespedes": reserva.cantidad_huespedes,
                        "monto": str(reserva.monto),
                    }
                })

            # Si no entendimos la elección
            save_state(request, state)
            return JsonResponse({
                "success": True,
                "stage": "confirm",
                "message": "No entendí tu elección. Por favor, indica el número de habitación de la lista o escribe 'otra' para cambiar criterios.",
                "options": data.get('opciones', []),
                "data": data,
            })

        # Fallback: flujo conversacional general
        save_state(request, state)
        return JsonResponse({
            "success": True,
            "stage": state['stage'],
            "message": "¿En qué puedo ayudarte? Puedo asistirte a reservar si me das fechas (YYYY-MM-DD), tipo(s) (simple/doble/suite/presidencial) y cantidad de huéspedes.",
            "entities": extracted,
            "data": data,
        })

    except Exception as e:
        return JsonResponse({"success": False, "message": f"Error: {str(e)}"}, status=500)