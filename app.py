import json
import os
import hmac
import re
import hashlib
import threading
import time
import pytz
import redis
import datetime as dt
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from config.celery_app import celery
from components.twilio_component import TwilioManager
from components.openai_component import OpenAIManager
from components.calendar_component import GoogleCalendarManager
from components.database.database_mongodb_component import DataBaseMongoDBManager
from components.database.database_mysql_component import DataBaseMySQLManager
from helpers.helpers import format_number, extraer_json, json_a_lista

# Configuración de Redis
r = redis.Redis(host='localhost', port=6379, db=0)

# Inicializar Flask
app = Flask(__name__)

# Inicializar Componentes
twilio = TwilioManager()
openai = OpenAIManager()
calendar = GoogleCalendarManager()
dbMongoManager = DataBaseMongoDBManager()
dbMySQLManager = DataBaseMySQLManager()

# Manejo de tareas en Redis
def get_scheduled_task_id(celular):
    """Devuelve el ID de la tarea pendiente para este celular, o None."""
    return r.get(f"celery_task:{celular}")

def set_scheduled_task_id(celular, task_id):
    """Guarda en Redis el ID de la tarea Celery pendiente para este celular."""
    if task_id:
        r.set(f"celery_task:{celular}", task_id, ex=300)  # Expira en 5 minutos

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

@celery.task
def enviar_respuesta(cliente_mysql, conversacion_id_mysql):
    celular = cliente_mysql["celular"]
    nombre = cliente_mysql["nombre"]
    cliente_id_mysql = cliente_mysql["cliente_id"]
    motivo_actual=cliente_mysql['motivo']
    estado_actual = cliente_mysql['estado']
    
    print("Enviando respuesta a:", celular)
    
    campanha_registro = dbMySQLManager.asociar_cliente_a_campana_mas_reciente(cliente_id_mysql)
    campanha = campanha_registro["descripcion"] if campanha_registro else ""
    
    dbMySQLManager.actualizar_fecha_ultima_interaccion(cliente_id_mysql, datetime.now(pytz.utc))
    
    conversation_actual = dbMongoManager.obtener_conversacion_actual(celular)
    print("Conversación actual:", conversation_actual)
    
    max_intentos = 5
    intento_actual = 0
    while intento_actual < max_intentos:
        try:
            motivo = openai.clasificar_motivo(conversation_actual)
            print("Intención detectada antes extraer json:", motivo)
            motivo = extraer_json(motivo)
            
            if motivo:
                print("Motivo detectado:", motivo)
                motivo_list = json_a_lista(motivo)

                if motivo_list[0] == 4:
                    lima_tz = pytz.timezone("America/Lima")
                    date = datetime.now(lima_tz) + timedelta(days=3)
                    date_str = date.strftime("%Y-%m-%d %H:%M")
                    reserva_cita = calendar.reservar_cita(date_str, summary=f"Cita reservada para {nombre}", duration_minutes=15)
                    
                    if reserva_cita and "start" in reserva_cita and "dateTime" in reserva_cita["start"]:
                        utc_tz = pytz.utc
                        date_lima = datetime.fromisoformat(reserva_cita["start"]["dateTime"]).astimezone(utc_tz)
                        date_bd = date_lima.strftime('%Y-%m-%d %H:%M:%S')
                        dbMySQLManager.insertar_cita(cliente_id_mysql, date_bd, "pendiente", conversacion_id_mysql)
                    else:
                        print("Error: No se pudo reservar la cita correctamente.")                  
                nuevo_motivo=name_motivo(motivo_list[0])
                nuevo_estado = name_estado(motivo_list[1])
                guardar_motivo(motivo_actual,nuevo_motivo,cliente_id_mysql,motivo_list[1])
                guardar_estado(estado_actual,nuevo_estado,cliente_id_mysql,"Cambio de estado: "+ nuevo_estado)
                response_message = openai.mensaje_personalizado(nuevo_motivo,nuevo_estado,detalle,conversation_actual)  
                print("Response message json:", response_message)
                twilio.send_message(celular, response_message)
                dbMongoManager.guardar_respuesta_ultima_interaccion_chatbot(celular, response_message)
                dbMySQLManager.actualizar_fecha_ultima_interaccion_bot(cliente_id_mysql, datetime.now(pytz.utc))
                clear_scheduled_task_id(celular)
                break
            else:
                raise ValueError("No se pudo extraer un motivo válido")
        except Exception as e:
            intento_actual += 1
            print(f"Error procesando intenciones (intento {intento_actual}/{max_intentos}): {e}")
            if intento_actual == max_intentos:
                response_message = "Lo siento, hubo un problema al procesar tu mensaje. Inténtalo más tarde."
                twilio.send_message(celular, response_message)
                dbMongoManager.guardar_respuesta_ultima_interaccion_chatbot(celular, response_message)
                dbMySQLManager.actualizar_fecha_ultima_interaccion_bot(cliente_id_mysql, datetime.now(pytz.utc))
                clear_scheduled_task_id(celular)
                break

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
            print(f"Revocando tarea anterior {old_task_id.decode('utf-8')} para {celular}")
            revoke_task(old_task_id.decode('utf-8'))  # Revocar tarea anterior
            clear_scheduled_task_id(celular)  # Eliminar de Redis

        # Llama a la tarea de Celery con un retraso de 2 segundos
        new_task = enviar_respuesta.apply_async(
            args=[cliente_mysql,conversacion_id_mysql],
            countdown=30
        )

        # 4) Guardar el task_id en Redis
        set_scheduled_task_id(celular, new_task.id)

        print(f"Tarea programada {new_task.id} para {celular}")

        return 'OK', 200

    except Exception as e:
        print("Error en whatsapp_bot:", e)
        return "Error interno del servidor", 500


def name_motivo(motivo_num):
    if motivo_num==1:
        return 'economico'
    elif motivo_num==2:
        return 'mala informacion'
    elif motivo_num==3:
        return 'administrativo'
    elif motivo_num==4:
        return 'olvido de pago'
    else:
        return 'desconocido'

def guardar_motivo(motivo_actual, nuevo_motivo, cliente_id_mysql, detalle):
    if nuevo_motivo and motivo_actual and es_motivo_valido(motivo_actual, nuevo_motivo):
        dbMySQLManager.insertar_motivo_historico_cliente(cliente_id_mysql, nuevo_motivo, detalle)
        dbMySQLManager.actualizar_motivo_cliente(cliente_id_mysql, nuevo_motivo)

def guardar_estado(estado_actual, nuevo_estado, cliente_id_mysql, detalle):
    if nuevo_estado and estado_actual and es_transicion_valida(estado_actual, nuevo_estado):
        dbMySQLManager.insertar_estado_historico_cliente(cliente_id_mysql, nuevo_estado, detalle)
        dbMySQLManager.actualizar_estado_cliente(cliente_id_mysql, nuevo_estado)

def es_motivo_valido(motivo_actual, nuevo_motivo):
    if motivo_actual == nuevo_motivo:
        return False  
    return True

def es_transicion_valida(estado_actual, nuevo_estado):
    if estado_actual=='finalizado':
        return False
    if nuevo_estado == estado_actual:
        return False  # No hay cambio de estado
    return True  # No permitir otras transiciones

if __name__ == '__main__':
    # Iniciar la aplicación Flask
    app.run(host='0.0.0.0',port=5000)
