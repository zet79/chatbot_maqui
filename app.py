import json
import threading
import time
import os
import hmac
import re
import hashlib
import redis
from datetime import datetime, timedelta
from config.celery_app import celery
from flask import Flask, request, jsonify
from components.twilio_component import TwilioManager
from components.openai_component import OpenAIManager
from components.calendar_component import GoogleCalendarManager
from components.database.database_mongodb_component import DataBaseMongoDBManager
from components.database.database_mysql_component import DataBaseMySQLManager
from helpers.helpers import format_number, extraer_json,json_a_lista
#from api_keys.api_keys import client_id_zoho, client_secret_zoho, refresh_token_zoho
r = redis.Redis(host='localhost', port=6379, db=0)

app = Flask(__name__)

# Inicializar Componentes
twilio = TwilioManager()
openai = OpenAIManager()
calendar = GoogleCalendarManager()
dbMongoManager = DataBaseMongoDBManager()
dbMySQLManager = DataBaseMySQLManager()
#culqi = CulqiManager()

def get_scheduled_task_id(celular):
    """Devuelve el ID de la tarea pendiente para este celular, o None."""
    return r.get(f"celery_task:{celular}")

def set_scheduled_task_id(celular, task_id):
    """Guarda en Redis el ID de la tarea Celery pendiente para este celular."""
    # ex=300 => expira en 5 minutos si por alguna razón no se limpia
    r.set(f"celery_task:{celular}", task_id, ex=300)

def clear_scheduled_task_id(celular):
    """Elimina la referencia en Redis de la tarea pendiente para este celular."""
    r.delete(f"celery_task:{celular}")

def revoke_task(task_id):
    """Revoca la tarea dado el task_id."""
    try:
        celery.control.revoke(task_id, terminate=True)
        print(f"Tarea {task_id} revocada exitosamente.")
    except Exception as e:
        print(f"Error revocando tarea: {e}")


# Función para enviar la respuesta al cliente después del retardo
@celery.task
def enviar_respuesta(cliente_mysql, conversacion_id_mysql):
    celular=cliente_mysql["celular"]
    cliente_id_mysql=cliente_mysql["cliente_id"]
    print("Enviando respuesta a:",celular )

    estado_actual = cliente_mysql['estado']
    campanha_registro =dbMySQLManager.asociar_cliente_a_campana_mas_reciente()
    campanha = campanha_registro["descripcion"] if campanha_registro != None else ""  

    dbMySQLManager.actualizar_fecha_ultima_interaccion(cliente_id_mysql, datetime.now())
    # Verificar si existe una conversación activa en MySQL para el cliente

    # Obtener la conversación actual del cliente
    conversation_actual = dbMongoManager.obtener_conversacion_actual(celular)

    # Obtener el historial de conversaciones del cliente en caso tenga
    # = dbMongoManager.obtener_historial_conversaciones(cliente["celular"]) esto no va

    print("Conversación actual:", conversation_actual)

    max_intentos = 5
    intento_actual = 0

    while intento_actual < max_intentos:
        try:
            motivo = openai.clasificar_motivo(conversation_actual)
            print("Intención detectada antes extraer json:", motivo)
            motivo = extraer_json(motivo)
            if motivo is not None:
                print("Motivo detectado:", motivo)
                # Generamos un mensaje de respuesta
                print("Cliente mysql", cliente_mysql)
                #motivo_list = intencion.split(")")
                motivo_list = json_a_lista(motivo)
                print("Intencion lista: ", motivo_list)
                if motivo_list[0] == 1:
                    nuevo_estado = 'en seguimiento'
                    if es_transicion_valida(estado_actual, nuevo_estado):                           
                        cliente_mysql["estado"] = nuevo_estado
                        dbMySQLManager.insertar_estado_historico_cliente(cliente_id_mysql, nuevo_estado,motivo_list[1])
                        dbMySQLManager.actualizar_estado_cliente(cliente_id_mysql, nuevo_estado)
                    else:
                        print(f"No se actualiza el estado desde {estado_actual} a {nuevo_estado}.")

                    response_message = "Gracias por responder a este mensaje. Entendemos su situación y estaremos en contacto con usted a través de nuestros asesores."
                elif motivo_list[0] == 2:
                    nuevo_estado = 'en seguimiento'
                    if es_transicion_valida(estado_actual, nuevo_estado):                           
                        cliente_mysql["estado"] = nuevo_estado
                        dbMySQLManager.insertar_estado_historico_cliente(cliente_id_mysql, nuevo_estado,motivo_list[1])
                        dbMySQLManager.actualizar_estado_cliente(cliente_id_mysql, nuevo_estado)
                    else:
                        print(f"No se actualiza el estado desde {estado_actual} a {nuevo_estado}.")

                    response_message = "Gracias por responder a este mensaje. Entendemos su situación y estaremos en contacto con usted a través de nuestros asesores."
                elif motivo_list[0]== 3:
                    nuevo_estado = 'en seguimiento'
                    if es_transicion_valida(estado_actual, nuevo_estado):                           
                        cliente_mysql["estado"] = nuevo_estado
                        dbMySQLManager.insertar_estado_historico_cliente(cliente_id_mysql, nuevo_estado,motivo_list[1])
                        dbMySQLManager.actualizar_estado_cliente(cliente_id_mysql, nuevo_estado)
                    else:
                        print(f"No se actualiza el estado desde {estado_actual} a {nuevo_estado}.")

                    response_message = "Gracias por responder a este mensaje. Entendemos su situación y estaremos en contacto con usted a través de nuestros asesores."
                elif motivo_list[0]== 4:

                    '''
                    print("Ingreso a la intencion 4")             
                    print("Fecha y hora máxima para el pago:", datetime.now()+3*24)
                    reserva_pago = calendar.reservar_cita(motivo_list[1].lstrip(), summary=f"Último día de pago reservado para {cliente_mysql['nombre']}",duration_minutes=15)
                    if not reserva_pago:
                        response_message = f"""{{"mensaje": "Hubo un error al agendar la fecha del pago. Por favor, intenta nuevamente."}}"""
                    elif reserva_pago == "Horario no disponible":
                        # Comprobar si esa cita es de el mismo cliente que hace la consulta
                        cita_cliente = dbMySQLManager.buscar_cita_por_fecha_cliente(cliente_id_mysql, motivo_list[1].lstrip())
                        response_message = openai.consultaCitaDelCliente(cliente_mysql,cita_cliente,conversation_actual,campanha)
                        response_message = f"""{{"mensaje": "Lo siento, el horario seleccionado no está disponible. Por favor, selecciona otro horario."}}"""
                    else:
                        nuevo_estado = 'promesas de pago'   
                        if es_transicion_valida(estado_actual, nuevo_estado) :
                            cliente_mysql["estado"] = 'promesas de pago'
                            dbMySQLManager.actualizar_estado_cliente(cliente_id_mysql, nuevo_estado)
                            dbMySQLManager.actualizar_estado_historico_cliente(cliente_id_mysql, nuevo_estado)
                        else:
                            print(f"No se actualiza el estado desde {estado_actual} a {nuevo_estado}.")

                        print("Cita reservada:", reserva_cita)
                        response_message = openai.consultaCitareservada(cliente_mysql,reserva_cita,conversation_actual,cliente_nuevo,campanha)
                
                        fecha_cita = datetime.fromisoformat(reserva_cita["start"]["dateTime"]).strftime('%Y-%m-%d %H:%M:%S')
                        # Registrar la cita en MySQL y vincularla con la conversación activa
                        dbMySQLManager.insertar_cita(
                            cliente_id=cliente_id_mysql,
                            fecha_cita=fecha_cita,
                            motivo="Consulta de cita",
                            estado_cita="agendada",
                            conversacion_id=conversacion_id_mysql
                        )
                    '''
                    nuevo_estado = 'promesa de pago'
                    if es_transicion_valida(estado_actual, nuevo_estado):                           
                        cliente_mysql["estado"] = nuevo_estado
                        dbMySQLManager.insertar_estado_historico_cliente(cliente_id_mysql, nuevo_estado,motivo_list[1])
                        dbMySQLManager.actualizar_estado_cliente(cliente_id_mysql, nuevo_estado)
                    else:
                        print(f"No se actualiza el estado desde {estado_actual} a {nuevo_estado}.")

                    response_message = "Gracias por responde a este mensaje. Uno de nuestros asesores le otorgará la información "
                    "y el código necesarios para el pago en unos momentos."

                else:
                    if es_transicion_valida(estado_actual, nuevo_estado):                           
                        cliente_mysql["estado"] = 'no interesado'
                        dbMySQLManager.insertar_estado_historico_cliente(cliente_id_mysql, nuevo_estado,motivo_list[1])
                        dbMySQLManager.actualizar_estado_cliente(cliente_id_mysql, nuevo_estado)
                    else:
                        print(f"No se actualiza el estado desde {estado_actual} a {nuevo_estado}.")

                    response_message = "Apreciamos su repuesta. Haremos lo posible por continuar ofreciendo un mejor servicio."
            else:
                response_message = "Lo siento, no pude entender tu mensaje. Por favor, intenta de nuevo."
                twilio.send_message(celular, response_message)
                dbMongoManager.guardar_respuesta_ultima_interaccion_chatbot(celular, response_message)
                dbMySQLManager.actualizar_fecha_ultima_interaccion_bot(cliente_id_mysql, datetime.now())
                clear_scheduled_task_id(celular)
                print(f"Terminó la tarea para {celular}, limpiando task_id en Redis.")
                break

        except Exception as e:
            intento_actual += 1
            print(f"Error procesando intenciones (intento {intento_actual}/{max_intentos}): {e}")
            if intento_actual == max_intentos:
                # Si llegamos al máximo de intentos, enviamos un mensaje genérico y salimos
                response_message = "Lo siento, hubo un problema al procesar tu mensaje. Por favor intenta más tarde."
                twilio.send_message(celular, response_message)
                dbMongoManager.guardar_respuesta_ultima_interaccion_chatbot(celular, response_message)
                dbMySQLManager.actualizar_fecha_ultima_interaccion_bot(cliente_id_mysql, datetime.now())
                
                clear_scheduled_task_id(celular)
                print(f"Terminó la tarea para {celular}, limpiando task_id en Redis.")
                break
            else:
                print("Reintentando desde la clasificación de intención...")
                # Continúa el bucle (vuelve al inicio) para intentar de nuevo

@app.route('/bot', methods=['POST'])
def whatsapp_bot():
    
    try:
        print("RESPUESTA DE TWILIO: ", request)
        print("RESPUESTA DE TWILIO FORM: ", request.form)
        print("RESPUESTA DE TWILIO BODY: ", request.form.get('Body'))
        print("Profile Name: ", request.form.get('ProfileName'))
        profileName = request.form.get('ProfileName')
        incoming_msg = request.form.get('Body').lower()
        sender = request.form.get('From')
        celular = sender.split('whatsapp:')[1]
        print("Mensaje recibido:", incoming_msg)
        print("Remitente:", celular)
        
        
        cliente = dbMongoManager.obtener_cliente_por_celular(celular)
        print("cliente_mongo:", cliente, type(cliente))
        if not cliente: 
            return

        #Buscar al cliente
        cliente_mysql = dbMySQLManager.obtener_cliente_por_celular(celular)
        print("cliente_mysql:", cliente_mysql, type(cliente_mysql))
        if not cliente_mysql:
            return 
        
        if cliente_mysql["nombre"] == "":
            cliente_mysql["nombre"] = profileName
            dbMySQLManager.actualizar_nombre_cliente(cliente_mysql["cliente_id"], profileName)
        
        if not dbMongoManager.hay_conversacion_activa(celular):
            # Se crea una conversacion activa, solo se crea
            print("Creando una nueva conversación activa para el cliente.")
            dbMongoManager.crear_conversacion_activa(celular)
        
        conversacion_mysql = dbMySQLManager.obtener_conversacion_activa(cliente_mysql["cliente_id"])
        if not conversacion_mysql:
            # Crear conversación activa en MySQL si no existe
            conversacion_id_mysql = dbMySQLManager.insertar_conversacion(
                cliente_id=cliente_mysql["cliente_id"],
                mensaje="Inicio de conversación",
                tipo_conversacion="activa",
                resultado=None,
                estado_conversacion="activa"
            )

        else:
            conversacion_id_mysql = conversacion_mysql["conversacion_id"]
        # Agrega la interacción del cliente a la conversación actual
        #dbMongoManager.guardar_mensaje_cliente_ultima_interaccion(celular, incoming_msg)
        
        dbMongoManager.crear_nueva_interaccion(celular, incoming_msg)
        print("Interacción del cliente guardada en la conversación actual.")  

        # Revisar si ya hay una tarea pendiente para este celular
        old_task_id = get_scheduled_task_id(celular)
        if old_task_id:
            # Revocar la tarea anterior para reiniciar el countdown
            revoke_task(old_task_id.decode('utf-8'))       

        # Llama a la tarea de Celery con un retraso de 2 segundos
        new_task = enviar_respuesta.apply_async(
            args=[cliente_mysql,conversacion_id_mysql],
            countdown=45
        )

        # 4) Guardar el task_id en Redis
        set_scheduled_task_id(celular, new_task.id)

        print(f"Tarea programada {new_task.id} para {celular}")

        return 'OK', 200

    except Exception as e:
        print("Error en whatsapp_bot:", e)
        return "Error interno del servidor", 500
'''
@app.route('/bot', methods=['POST'])
def whatsapp_bot():
    try:
        # Intentar obtener los datos del formulario (Twilio envía form-data)
        body = request.form.get('Body')
        profileName = request.form.get('ProfileName')
        sender = request.form.get('From')

        # Si no se encuentran datos en form, intenta obtenerlos como JSON
        if not body or not sender:
            data = request.get_json(silent=True)
            if data:
                # Algunos clientes pueden enviar el mensaje con otra clave (por ejemplo, "message")
                body = body or data.get('Body') or data.get('message')
                profileName = profileName or data.get('ProfileName')
                sender = sender or data.get('From')

        # Validar que se recibieron los datos necesarios
        if not body or not sender:
            print("Datos insuficientes en la solicitud:", request.data)
            return "Datos insuficientes", 400

        # Procesar los datos recibidos
        incoming_msg = body.lower()
        celular = sender.split('whatsapp:')[1]
        print("Mensaje recibido:", incoming_msg)
        print("Remitente:", celular)
        print("Profile Name:", profileName)

        # Resto de la lógica...
        cliente = dbMongoManager.obtener_cliente_por_celular(celular)
        if not cliente:
            return "Cliente no encontrado", 200

        cliente_mysql = dbMySQLManager.obtener_cliente_por_celular(celular)
        if not cliente_mysql:
            return "Cliente MySQL no encontrado", 200

        if cliente_mysql["nombre"] == "":
            cliente_mysql["nombre"] = profileName
            dbMySQLManager.actualizar_nombre_cliente(cliente_mysql["cliente_id"], profileName)

        if not dbMongoManager.hay_conversacion_activa(celular):
            print("Creando una nueva conversación activa para el cliente.")
            dbMongoManager.crear_conversacion_activa(celular)

        conversacion_mysql = dbMySQLManager.obtener_conversacion_activa(cliente_mysql["cliente_id"])
        if not conversacion_mysql:
            conversacion_id_mysql = dbMySQLManager.insertar_conversacion(
                cliente_id=cliente_mysql["cliente_id"],
                mensaje="Inicio de conversación",
                tipo_conversacion="activa",
                resultado=None,
                estado_conversacion="activa"
            )
        else:
            conversacion_id_mysql = conversacion_mysql["conversacion_id"]

        dbMongoManager.crear_nueva_interaccion(celular, incoming_msg)
        print("Interacción del cliente guardada en la conversación actual.")

        old_task_id = get_scheduled_task_id(celular)
        if old_task_id:
            revoke_task(old_task_id.decode('utf-8'))

        new_task = enviar_respuesta.apply_async(
            args=[cliente_mysql, conversacion_id_mysql],
            countdown=45
        )
        set_scheduled_task_id(celular, new_task.id)
        print(f"Tarea programada {new_task.id} para {celular}")

        return 'OK', 200

    except Exception as e:
        print("Error en whatsapp_bot:", e, flush=True)
        return "Error interno del servidor", 500
'''


def es_transicion_valida(estado_actual, nuevo_estado):
    '''
    prioridad_estados = {
        'pendiente de contacto': 1,
        'seguimiento': 2,
        'interesado': 3,
        'promesas de pago': 4,
        'cita agendada': 5,
        'finalizado': 6,
        'no interesado': 0,
        'inactivo': 0
    }
    if estado_actual== 'no interesado' and nuevo_estado == 'no interesado':
        return True    
    '''


    if nuevo_estado == estado_actual:
        return False  # No hay cambio de estado

    '''
    # Permitir avanzar a un estado de mayor prioridad
    if prioridad_estados.get(nuevo_estado, -1) > prioridad_estados.get(estado_actual, -1):
        return True
    '''

    '''
    # Permitir transiciones específicas desde 'finalizado' a ciertos estados
    if estado_actual == 'finalizado' and nuevo_estado in ['seguimiento', 'interesado']:
        return True  # Permitir volver a 'seguimiento' o 'interesado' desde 'finalizado'

    # Permitir transiciones a 'no interesado' o 'inactivo' solo desde 'seguimiento' o 'interesado'
    if estado_actual in ['seguimiento', 'interesado'] and nuevo_estado in ['no interesado', 'inactivo']:
        return True  # Permitir cambiar a 'no interesado' o 'inactivo' desde 'seguimiento' o 'interesado'
    '''
    return True  # No permitir otras transiciones


def obtener_cliente_id_por_charge(charge):
    # Supongamos que usas 'metadata' para guardar el 'cliente_id'
    cliente_id = charge.get('metadata', {}).get('cliente_id')
    return cliente_id

@celery.task
def procesar_culqi_webhook(data):
    try:
        # Procesar el contenido de la notificación
        evento = data.get('type')
        if evento == 'charge.creation.succeeded':  # Verifica si es el evento correcto
            charge = data.get('data', {})
            first_name = charge.get('antifraudDetails', {}).get('firstName')
            last_name = charge.get('antifraudDetails', {}).get('lastName')
            phone_number = charge.get('antifraudDetails', {}).get('phone')
            phone_number = format_number(phone_number) if phone_number else None

            if phone_number:
                cliente_id = dbMySQLManager.obtener_id_cliente_por_celular(phone_number)
                if cliente_id:
                    monto = charge.get('amount', 0) / 100  # Convertir céntimos a unidades
                    metodo_pago = "link de pago"
                    dbMySQLManager.agregar_pago_y_confirmar_cita(cliente_id, monto, metodo_pago,first_name,last_name)

                    # Actualiza Google Calendar y envía confirmación al cliente
                    cita = dbMySQLManager.obtener_cita_mas_cercana(cliente_id)
                    if cita:
                        fecha_cita = datetime.fromisoformat(cita['fecha_cita'])
                        fecha = fecha_cita.strftime("%Y-%m-%d")
                        hora_inicio = fecha_cita.strftime("%H:%M")
                        calendar.actualizar_evento_a_confirmado(fecha, hora_inicio)

                    # Enviar mensaje de confirmación
                    response_message = "¡Gracias por tu pago! Tu cita ha sido confirmada. Te esperamos."
                    twilio.send_message(phone_number, response_message)

                    # Actualizar interacción
                    fecha_actual = datetime.now()
                    dbMySQLManager.actualizar_fecha_ultima_interaccion_bot(cliente_id, fecha_actual)
                    dbMongoManager.guardar_respuesta_ultima_interaccion_chatbot(phone_number, response_message)
                else:
                    print("Cliente no encontrado para el número:", phone_number)
            else:
                print("Número de teléfono no encontrado en antifraudDetails.")
        else:
            print(f"Evento no manejado: {evento}")
    except Exception as e:
        print("Error procesando webhook de Culqi:", e)

@app.route('/culqi-webhook', methods=['POST'])
def culqi_webhook():
    try:
        data = request.get_json()
        print("Notificación recibida:", data)

        # Llama a la tarea Celery para procesar la notificación
        procesar_culqi_webhook.apply_async(args=[data])

        return '', 200
    except Exception as e:
        print("Error en culqi_webhook:", e)
        return 'Error interno del servidor', 500


#@app.route('/culqi-webhook', methods=['POST'])
#def culqi_webhook():
#    try:
#        # Procesar el contenido de la notificación
#        data = request.get_json()
#        evento = data.get('type')
#        print("data : ", data)
#        
#        if evento == 'charge.creation.succeeded':  # Verifica si es el evento correcto
#            # Parsear los datos del objeto `charge` dentro de `data`
#            charge_data = data.get('data', {})
#            charge = charge_data if isinstance(charge_data, dict) else json.loads(charge_data)  # Deserializar si es string
#            
#            # Obtener el número de teléfono desde antifraudDetails
#            phone_number = charge.get('antifraudDetails', {}).get('phone')
#            phone_number = format_number(phone_number) if phone_number else None
#            if phone_number:
#                # Buscar al cliente en la base de datos por número de teléfono
#                cliente_id = dbMySQLManager.obtener_id_cliente_por_celular(phone_number)
#                if cliente_id:
#                    # Actualizar el estado del cliente a 'cita agendada'
#                    dbMySQLManager.actualizar_estado_cliente(cliente_id, 'cita agendada')
#                    
#                    # Registrar el pago y confirmar la cita
#                    monto = charge.get('amount', 0) / 100  # Culqi maneja el monto en céntimos, convertir a unidades monetarias
#                    metodo_pago = "link de pago"
#                    dbMySQLManager.agregar_pago_y_confirmar_cita(cliente_id, monto, metodo_pago)
#                    
#                    # marcar cita en calendar como  "Cita confirmada para {cliente_mysql['nombre']}"
#                    cita = dbMySQLManager.obtener_cita_mas_cercana(cliente_id)
#                    if not cita:
#                        print("No se encontró una cita para el cliente:", phone_number)
#                       # Enviar mensaje de confirmación al cliente
#                        response_message = "¡Gracias por tu pago! Tu cita ha sido confirmada. Te esperamos."
#                        twilio.send_message(phone_number, response_message)

#                        # Actualizar fechas de última interacción
#                        fecha_actual = datetime.now()
#                        dbMySQLManager.actualizar_fecha_ultima_interaccion_bot(cliente_id, fecha_actual)
#                        dbMongoManager.guardar_respuesta_ultima_interaccion_chatbot(phone_number, response_message)
#
#                    fecha_cita = cita['fecha_cita']  # Formato 'YYYY-MM-DD HH:MM:SS'
#
#                    # Formatear la fecha y hora para el método de confirmacion
#                    fecha = fecha_cita.strftime("%Y-%m-%d")
#                    hora_inicio = fecha_cita.strftime("%H:%M")
#
#                    print(f"Procesando cita agendada: {fecha} {hora_inicio} del cliente {cita["cliente_id"]}")
#
#                    # Llamar al método para editar el evento
#                    evento_editado = calendar.actualizar_evento_a_confirmado(fecha, hora_inicio)
#                    if evento_editado:
#                        print("Evento confirmado exitosamente.")
#                    else:
#                        print("No se encontró ningún evento en el rango especificado.")                    
#
#                    # Enviar mensaje de confirmación al cliente
#                    response_message = "¡Gracias por tu pago! Tu cita ha sido confirmada. Te esperamos."
#                    twilio.send_message(phone_number, response_message)
#
#                    # Actualizar fechas de última interacción
#                    fecha_actual = datetime.now()
#                    dbMySQLManager.actualizar_fecha_ultima_interaccion_bot(cliente_id, fecha_actual)
#                    dbMongoManager.guardar_respuesta_ultima_interaccion_chatbot(phone_number, response_message)
#                else:
#                    print("No se encontró un cliente con el número de teléfono:", phone_number)
#            else:
#                print("No se encontró el número de teléfono en antifraudDetails")
#
#        else:
#            print(f"Evento no manejado: {evento}")
#
#        return '', 200
#
#    except Exception as e:
#        print("Error en culqi_webhook:", e)
#        return 'Error interno del servidor', 500



if __name__ == '__main__':
    # Iniciar la aplicación Flask
    app.run(host='0.0.0.0',port=5000)
