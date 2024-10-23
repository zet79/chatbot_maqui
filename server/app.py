from flask import Flask, request
from twilio.rest import Client
from openai import OpenAI
from datetime import datetime, time, timedelta
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_calendar_class import GoogleCalendarManager
import pandas as pd
from helpers import extract_datetime, formatear_fecha_hora
from promp import prompt_inicial
from api_keys import openai_api_key, account_sid, auth_token
import locale

# Establecer la localización en español
locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
app = Flask(__name__)

# Configuración Twilio
client = Client(account_sid, auth_token)

# Configuración 
conversation_history = """Historial de conversación: El cliente está interesado en obtener información sobre trasplante capilar y tratamientos faciales. 
                        Se están abordando sus dudas respecto a los procedimientos, tiempos de recuperación y otros detalles importantes."""

# Configuración Google Calendar API

calendar = GoogleCalendarManager()

# Función para manejar consultas usando OpenAI
def consult_product(user_question):
    print(user_question)
    global conversation_history
    client = OpenAI(api_key=openai_api_key)

    # Nueva llamada a la API de OpenAI para completar el mensaje
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages = [
            {"role": "system", "content": prompt_inicial},
            {"role": "user", "content": conversation_history + f"\nUser: {user_question}"}
        ],
        max_tokens=100,
    )

    # Obtener la respuesta
    response_message = response.choices[0].message.content
    
    if "primera pregunta" in conversation_history:
        horarios = obtener_horarios_disponibles()
        response_message += f"\nPor cierto, estos son los horarios disponibles para una consulta durante esta semana: \n{(horarios)}"
        conversation_history += "primera pregunta"

    conversation_history += f"\nUser: {user_question}\nAI: {response_message}"
    print(conversation_history)
    return response_message

# Función para agendar citas en Google Calendar
def schedule_appointment(user_date, user_time, nombre_cliente, celular_cliente):
    try:
        print("Parametros agendar una cita",user_date, user_time)
        start_time = datetime.strptime(f"{user_date} {user_time}", "%Y-%m-%d %H:%M")
        end_time = start_time + timedelta(hours=1)

        # Verificar si el horario está disponible
        calendar.list_upcoming_events()

        fecha, hora = formatear_fecha_hora(user_date, user_time)

        if calendar.is_time_available(start_time, end_time):
            print("Horario disponible.")
            # Crear el evento en Google Calendar
            summary = f"Cita con {nombre_cliente} (Tel: {celular_cliente})"
            timezone = "America/Lima"

            calendar.create_event(
                summary=summary,
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                timezone=timezone
            )

            return f"¡Cita agendada! Te esperamos el {fecha} a las {hora}. ¿Hay algo más en lo que pueda ayudarte?"
        else:
            return f"Lo siento, ese horario ya está ocupado. Por favor, elige otro horario."

    except HttpError as error:
        return f"Hubo un error al agendar la cita: {error}"


# Leer el archivo Excel
def leer_datos_excel():
    df = pd.read_excel('clientes.xlsx')
    return df


def iniciar_conversacion():
    df = leer_datos_excel()  # Leer datos desde el Excel
    global conversation_history
    for index, row in df.iterrows():
        nombre = row['Nombre']
        apellido = row['Apellido']
        celular = str(row['Celular']).strip()

        # Formatear correctamente el número
        if not celular.startswith('+'):
            celular = f'+{celular}'

        # Mensaje proactivo
        mensaje = f"Hola {nombre}, ¿cómo estás? Soy parte del equipo de Trasplante Capilar. Hemos notado que podrías estar interesado en nuestros tratamientos capilares. Si tienes alguna duda, quieres más información, o prefieres agendar una cita, estoy aquí para ayudarte."

        # Enviar mensaje usando Twilio
        client.messages.create(
            body=mensaje,
            from_='whatsapp:+14155238886',
            to=f'whatsapp:{celular}'
        )
        conversation_history += f"\nAI: {mensaje}"
        print(f"Mensaje enviado a {nombre} {apellido} al número {celular}")

def obtener_horarios_disponibles():
    # Consultar Google Calendar para obtener los horarios disponibles de esta semana
    horarios_disponibles = calendar.listar_horarios_disponibles()

    # Inicializar una cadena vacía para los horarios formateados
    horarios_formateados = ""

    # Diccionario para agrupar los horarios por día
    horarios_por_dia = {}

    for horario in horarios_disponibles:
        # Eliminar espacios adicionales al inicio y al final
        start_time, end_time = horario.strip().split(" - ")

        # Convertir a objeto datetime, eliminando posibles espacios extra
        start_time = start_time.strip()
        end_time = end_time.strip()

        # Corregir la conversión de cadena a datetime
        start_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M')
        end_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M')

        # Convertir el formato de 24 horas a AM/PM manualmente
        def convertir_a_am_pm(hora):
            if hora.hour < 12:
                return f"{hora.hour}:{hora.strftime('%M')} a.m."
            elif hora.hour == 12:
                return f"12:{hora.strftime('%M')} p.m."
            else:
                return f"{hora.hour - 12}:{hora.strftime('%M')} p.m."

        start_hour = convertir_a_am_pm(start_dt)
        end_hour = convertir_a_am_pm(end_dt)

        # Formatear el día y agrupar por día en el diccionario
        dia = start_dt.strftime('%A %d de %B').capitalize()
        if dia not in horarios_por_dia:
            horarios_por_dia[dia] = []
        horarios_por_dia[dia].append(f"{start_hour} a {end_hour}")

    # Formatear la salida final con los días y horarios agrupados
    for dia, rangos_horarios in horarios_por_dia.items():
        # Añadir el día y los horarios disponibles a la cadena
        horarios_formateados += f"{dia}:\n"
        for rango in rangos_horarios:
            horarios_formateados += f"  {rango}\n"

    print(horarios_formateados)

    if not horarios_formateados:
        return "No hay horarios disponibles en este momento."
    else:
        return horarios_formateados.strip()  # Elimina cualquier salto de línea adicional al final





def es_horario_laboral(fecha, hora):
    """ Verifica si la fecha y hora están dentro del horario laboral permitido. """
    # Verificar si el día es de lunes a viernes
    if fecha.weekday() >= 5:  # 5 = sábado, 6 = domingo
        return False
    
    # Verificar si la hora está entre 9 a.m. y 1 p.m. o entre 2 p.m. y 7 p.m.
    horario_inicio_1 = time(9, 0)
    horario_fin_1 = time(13, 0)
    horario_inicio_2 = time(14, 0)
    horario_fin_2 = time(19, 0)

    if (horario_inicio_1 <= hora <= horario_fin_1) or (horario_inicio_2 <= hora <= horario_fin_2):
        return True
    return False


def clasificar_intencion(mensaje):
    # Llamada a la API de OpenAI para clasificar la intención
    client = OpenAI(api_key=openai_api_key)
    global conversation_history
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": 
                    """
            Eres un asistente virtual especializado en tratamientos capilares y trasplantes para una clínica. 
            Tu objetivo es identificar la intención del usuario entre las siguientes opciones:
            - **Agendar una cita con fecha y hora específicas**: El usuario menciona una fecha y/o hora específica para agendar una cita.
            - **Agendar una cita sin especificar fecha y hora**: El usuario expresa que quiere agendar una cita, pero no menciona fecha ni hora. Deberías ofrecerle los horarios disponibles para la semana.
            - **Hacer una consulta sobre tratamientos**: El usuario hace preguntas o tiene dudas sobre los tratamientos capilares, trasplantes, o detalles relacionados, o  simplemente puede ser un saludo.
            
            Solo debes responder con la intención correspondiente y nada más. Las respuestas permitidas son: 'agendar una cita sin fecha', 'agendar una cita con fecha', 'hacer una consulta' y 'otros' en caso no encaje con ninguna de las intenciones mencionadas.
                Solo respondeme con las respuestas permitidas recuerda. SOLO ESAS. las cuales son :
                - agendar una cita sin fecha
                - agendar una cita con fecha
                - hacer una consulta
                - otros
                """
             },
            {"role": "user", "content": conversation_history + f"\nUser: {mensaje}"}
        ]
    )
    print("Conversation history",conversation_history)
    # Extraer la intención de la respuesta de OpenAI
    conversation_history += f"\nUser: {mensaje}\n"
    intencion = response.choices[0].message.content.strip().lower()
    return intencion

@app.route('/bot', methods=['POST'])
def whatsapp_bot():
    incoming_msg = request.form.get('Body').lower()
    sender = request.form.get('From')

    sender_num = sender.replace('whatsapp:+', '').strip()
    # Leer los datos del cliente desde el archivo Excel
    df = leer_datos_excel()
    print("Datos de los clientes:", df.info())
    print("Número de teléfono del cliente:", sender_num,sender_num.__len__())
    # Buscar al cliente en el Excel usando su número de teléfono
    df['Celular'] = df['Celular'].astype(str)
    cliente = df[df['Celular'] == sender_num].iloc[0]
    nombre_cliente = cliente['Nombre']
    celular_cliente = cliente['Celular']

    # Clasificar la intención usando OpenAI
    intencion = clasificar_intencion(incoming_msg)
    print("Intención clasificada:", intencion)

    if intencion == "agendar una cita sin fecha":
        horarios = obtener_horarios_disponibles()
        response_message = f"¡Perfecto! Estos son los horarios disponibles para esta semana:\n{(horarios)}\n¿Te queda bien alguno de estos? Si no, dime qué día te vendría mejor."
    
    elif intencion == "agendar una cita con fecha":
        # Extraer fecha y hora del mensaje
        user_date_str, user_time_str = extract_datetime(incoming_msg)
        print("Fecha y hora extraídas antes de formatear:", user_date_str, user_time_str)
        fecha, hora = formatear_fecha_hora(user_date_str, user_time_str)
        print("Fecha y hora extraídas:", fecha, hora)
        if user_date_str and user_time_str:
            # Convertir las cadenas de texto en objetos de fecha y hora
            user_date = datetime.strptime(user_date_str, '%Y-%m-%d').date()
            user_time = datetime.strptime(user_time_str, '%H:%M').time()

            # Verificar si está dentro del horario laboral
            if es_horario_laboral(user_date, user_time):
                response_message = schedule_appointment(user_date_str, user_time_str, nombre_cliente, celular_cliente)
            else:
                horarios = obtener_horarios_disponibles()
                response_message = f"No atendemos en ese horario. Nuestro horario es de lunes a viernes, de 9 a.m. a 1 p.m. y de 2 p.m. a 7 p.m. Estos son los horarios disponibles:\n{horarios}"
        else:
            response_message = "No pude entender la fecha y hora. Por favor, usa el formato AAAA-MM-DD HH:MM."

    elif intencion == "hacer una consulta" or intencion == "otros":
        response_message = consult_product(incoming_msg)
        client.messages.create(body=response_message, from_='whatsapp:+14155238886', to=sender)
        return 'OK', 200
    
    else:
        response_message = "Lo siento, no entendí tu solicitud. Por favor, dime si te gustaría agendar una cita o si tienes alguna duda sobre nuestros tratamientos capilares."

    client.messages.create(body=response_message, from_='whatsapp:+14155238886', to=sender)
    return 'OK', 200

if __name__ == '__main__':
    iniciar_conversacion()
    app.run(debug=True, port=5000)
