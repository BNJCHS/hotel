import os
import json
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.utils.dateparse import parse_date
from django.db.models import Q
from habitaciones.models import Habitacion, TipoHabitacion
from reservas.models import Reserva
from administracion.models import Servicio, Plan, Promocion

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
        lower_msg = message.lower()
        # Detectar intención de reservar por palabras clave aunque falten datos
        reservar_kw = any(k in lower_msg for k in [
            'reserv', 'book', 'quiero reservar', 'hacer una reserva', 'necesito reservar'
        ])
        intent_val = "reservar" if (ci and co and (tipo or cant)) or reservar_kw else "consulta"
        data = {
            "intent": intent_val,
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
    qs = Habitacion.objects.filter(
        disponible=True,
        en_mantenimiento=False,
        tipo_habitacion__activo=True,
        tipo_habitacion__capacidad__gte=capacidad_min,
    )
    if tipos:
        normalized = []
        for t in tipos:
            if not t:
                continue
            tnorm = str(t).strip().lower()
            if tnorm in ['simple', 'doble', 'suite', 'presidencial']:
                normalized.append(tnorm.capitalize())
            else:
                normalized.append(t)
        qs = qs.filter(tipo_habitacion__nombre__in=normalized)

    if check_in and check_out:
        overlapping_ids = list(
            Reserva.objects.filter(
                habitacion_asignada__in=qs.values_list('id', flat=True),
                check_in__lt=check_out,
                check_out__gt=check_in,
                estado__in=['confirmada', 'activa']
            ).values_list('habitacion_asignada_id', flat=True)
        )
        qs = qs.exclude(id__in=overlapping_ids)

    rooms = qs.order_by('tipo_habitacion__precio', 'numero')[:limit]
    return list(rooms)


# -------------------- Vista principal con flujo paso a paso --------------------

# -------------------- Q&A sobre el hotel --------------------

def _list_servicios():
    try:
        nombres = list(Servicio.objects.values_list('nombre', flat=True))
        return [n for n in nombres if n]
    except Exception:
        return []


def answer_hotel_question(message: str) -> str | None:
    """Responde preguntas frecuentes sobre el hotel con reglas simples y datos del sitio.
    Devuelve None si no encuentra una respuesta clara.
    """
    if not message:
        return None
    txt = message.lower()

    # Comunes de reserva: redirigir a flujo
    if any(k in txt for k in ["precio", "coste", "cuanto cuesta", "tarifa", "valor"]):
        return (
            "Los precios varían según fechas, tipo de habitación y disponibilidad. "
            "Si quieres, te ayudo a consultarlo: dime tus fechas (YYYY-MM-DD a YYYY-MM-DD), "
            "el tipo (simple/doble/suite/presidencial) y la cantidad de huéspedes."
        )

    # Check-in / Check-out
    if any(k in txt for k in ["check-in", "check in", "entrada", "ingreso", "llegada"]) and not any(k in txt for k in ["check-out", "check out", "salida"]):
        return "El check-in es a partir de las 15:00."
    if any(k in txt for k in ["check-out", "check out", "salida"]) and not any(k in txt for k in ["check-in", "check in", "entrada", "ingreso", "llegada"]):
        return "El check-out es hasta las 11:00."
    if any(k in txt for k in ["check-in", "check in", "entrada"]) and any(k in txt for k in ["check-out", "check out", "salida"]):
        return "El check-in es a partir de las 15:00 y el check-out hasta las 11:00."

    # Ubicación / contacto
    if any(k in txt for k in ["direccion", "dirección", "donde estan", "dónde están", "ubicacion", "ubicación", "como llegar", "cómo llegar", "telefono", "teléfono", "contacto"]):
        return (
            "Puedes encontrar nuestra dirección, mapa y datos de contacto en la página de Contacto: "
            "/contacto/. Si deseas, puedo ayudarte con una reserva ahora mismo."
        )

    # Servicios y amenidades
    if any(k in txt for k in ["servicios", "amenidades", "amenities", "que ofrecen", "qué ofrecen"]):
        servicios = _list_servicios()
        if servicios:
            listado = ", ".join(servicios[:15]) + ("…" if len(servicios) > 15 else "")
            return f"Ofrecemos: {listado}. ¿Te gustaría reservar o conocer disponibilidad?"
        return "Contamos con Wi‑Fi gratuito, desayuno disponible, estacionamiento sujeto a disponibilidad y piscina. ¿Te ayudo a reservar?"

    # Wi‑Fi
    if any(k in txt for k in ["wifi", "wi-fi", "wi fi"]):
        return "Sí, ofrecemos Wi‑Fi gratuito en todo el hotel."

    # Desayuno
    if "desayuno" in txt:
        return "El desayuno está disponible. En algunas tarifas puede estar incluido y en otras tiene costo adicional."

    # Estacionamiento
    if any(k in txt for k in ["estacionamiento", "parking", "aparcamiento"]):
        servicios = _list_servicios()
        if any("estacion" in s.lower() or "parking" in s.lower() for s in servicios):
            return "Disponemos de estacionamiento (sujeto a disponibilidad)."
        return "Contamos con estacionamiento sujeto a disponibilidad."

    # Piscina / Spa / Gimnasio
    if any(k in txt for k in ["piscina", "pileta"]):
        return "Sí, contamos con piscina. Los horarios pueden variar según la temporada."
    if any(k in txt for k in ["spa", "masajes"]):
        return "Disponemos de spa con servicios bajo reserva. ¿Te gustaría agendar durante tu estadía?"
    if any(k in txt for k in ["gimnasio", "gym", "fitness"]):
        return "Tenemos gimnasio disponible para huéspedes."

    # Mascotas
    if any(k in txt for k in ["mascotas", "pet", "perros", "gatos"]):
        return "La admisión de mascotas está sujeta a disponibilidad y condiciones. Consulta con recepción para más detalles."

    # Políticas de cancelación
    if any(k in txt for k in ["cancel", "cancelar", "cancelación", "politica", "política"]):
        return "Manejamos políticas flexibles según la tarifa. Si reservas aquí, te indicaremos las condiciones antes de confirmar."

    # Horarios generales
    if any(k in txt for k in ["horario", "a que hora", "a qué hora", "cuando abren", "cuándo abren"]):
        return "Nuestros horarios varían según el servicio. ¿Sobre qué servicio te gustaría saber el horario? (recepción, piscina, spa, restaurante)"

    # Niños / Cunas
    if any(k in txt for k in ["niños", "ninos", "cuna", "familia", "menores"]):
        return "Recibimos familias y contamos con opciones para niños según disponibilidad. Podemos preparar cunas bajo solicitud."

    # Default sin coincidencia
    return None


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

        # Saludo/greeting explícito: ofrecer menú inicial
        lower_msg = message.strip().lower()
        greeting_words = ["hola", "buenas", "buen día", "buen dia", "buenas tardes", "buenas noches", "hey", "holi"]
        if any(lower_msg == g or lower_msg.startswith(g+" ") for g in greeting_words):
            return JsonResponse({
                "success": True,
                "stage": "greeting",
                "message": "¡Hola! ¿Qué te gustaría saber del hotel? Puedo responder preguntas sobre servicios, horarios de check‑in/out, ubicación/contacto, desayuno y estacionamiento.",
            })

        # MODO SOLO Q&A: responder preguntas y, si es genérico, pedir especificar el tema
        answer = answer_hotel_question(message)
        if answer:
            return JsonResponse({
                "success": True,
                "stage": "answer",
                "message": answer,
            })
        # Consulta genérica: invitar a especificar
        consulta_generica_largas = ['tengo una consulta', 'tengo una pregunta', 'tengo una duda']
        consulta_generica_palabras = ['consulta', 'pregunta', 'duda']
        if (
            any(p in lower_msg for p in consulta_generica_largas) or
            any(
                lower_msg == w or lower_msg.startswith(w + ' ') or lower_msg.endswith(' ' + w) or (' ' + w + ' ') in lower_msg
                for w in consulta_generica_palabras
            )
        ):
            return JsonResponse({
                "success": True,
                "stage": "greeting",
                "message": "Claro, ¿sobre qué te gustaría saber del hotel? Por ejemplo: horarios de check‑in/out, servicios, ubicación/contacto, desayuno o estacionamiento.",
            })

        # Si no se reconoce la pregunta, pedir reformular
        return JsonResponse({
            "success": True,
            "stage": "greeting",
            "message": "No estoy seguro de haber entendido. ¿Podrías especificar tu consulta? Por ejemplo: horarios de check‑in/out, servicios, ubicación/contacto, desayuno o estacionamiento.",
        })

        # Extraer entidades del mensaje
        extracted = extract_intent_and_entities(message)
        intent = extracted.get('intent', 'otro')

        # Q&A del hotel si es una consulta
        if intent == 'consulta':
            answer = answer_hotel_question(message)
            if answer:
                # No alteramos el estado del flujo de reserva
                return JsonResponse({
                    "success": True,
                    "stage": "answer",
                    "message": answer,
                })
            # Si es una consulta genérica sin tema, pedir que especifique
            consulta_generica_largas = ['tengo una consulta', 'tengo una pregunta', 'tengo una duda']
            consulta_generica_palabras = ['consulta', 'pregunta', 'duda']
            if (
                any(p in lower_msg for p in consulta_generica_largas) or
                any(
                    lower_msg == w or lower_msg.startswith(w + ' ') or lower_msg.endswith(' ' + w) or (' ' + w + ' ') in lower_msg
                    for w in consulta_generica_palabras
                )
            ):
                return JsonResponse({
                    "success": True,
                    "stage": "greeting",
                    "message": "Claro, ¿sobre qué te gustaría saber del hotel? Por ejemplo: horarios de check‑in/out, servicios, ubicación/contacto, desayuno o estacionamiento.",
                })

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
        if choice is not None:
            data['eleccion'] = str(choice)

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
                    tipo_habitacion=room.tipo_habitacion,
                    habitacion_asignada=room,
                    check_in=check_in,
                    check_out=check_out,
                    cantidad_huespedes=int(data['cantidad_huespedes']),
                    estado='confirmada',
                )

                # Resetear estado tras crear
                reset_state(request)

                return JsonResponse({
                    "success": True,
                    "stage": "done",
                    "message": f"Reserva confirmada para la habitación {room.numero} ({room.tipo_habitacion.nombre}) del {check_in} al {check_out}.",
                    "reserva": {
                        "id": reserva.id,
                        "habitacion": room.numero,
                        "tipo": room.tipo_habitacion.nombre,
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