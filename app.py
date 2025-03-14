import json
import os
import hmac
import re
import hashlib
import threading
import time
import pytz
import redis
from redlock import Redlock
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
# Configuración de Redlock para lock distribuido
dlm = Redlock([{"host": "localhost", "port": 6379, "db": 0}])

# Inicializar Flask
app = Flask(__name__)

# Inicializar Componentes
twilio = TwilioManager()
openai = OpenAIManager()
calendar = GoogleCalendarManager()
dbMongoManager = DataBaseMongoDBManager()
dbMySQLManager = DataBaseMySQLManager()
lock = threading.Lock()

# Manejo de tareas en Redis
def get_scheduled_task_id(celular):
    """Devuelve el ID de la tarea pendiente para este celular, o None."""
    return r.get(f"celery_task:{celular}")

def set_scheduled_task_id(celular, task_id):
    return r.set(f"celery_task:{celular}", task_id, nx=True, ex=1000)

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

# Funciones para el lock distribuido con reintentos
def acquire_lock(resource, ttl=10000):
    """
    Intenta adquirir un lock distribuido en el recurso dado.
    :param resource: Clave del recurso (por ejemplo, "lock:+51953983765")
    :param ttl: Tiempo de vida del lock en milisegundos.
    :return: El objeto lock si se adquiere, o None.
    """
    return dlm.lock(resource, ttl)

def acquire_lock_with_retry(celular, ttl=10000, max_wait=10, interval=0.1):
    """
    Intenta adquirir el lock distribuido para el usuario identificado por 'celular'
    durante un máximo de 'max_wait' segundos, reintentando cada 'interval' segundos.
    """
    resource = f"lock:{celular}"
    start_time = time.time()
    lock = None
    while (time.time() - start_time) < max_wait:
        lock = acquire_lock(resource, ttl)
        if lock:
            return lock
        time.sleep(interval)
    return None

def release_lock(lock):
    """Liberamos lock dist."""
    if lock:
        dlm.unlock(lock)


@celery.task(bind=True)
def cerrarConversacion(self, conversacion_id_mysql, conversacion_id_mongo, celular):
    task_id_actual = self.request.id
    # Verificar si esta tarea es la vigente
    stored = get_scheduled_task_id(f"cerrar_{celular}")
    if not stored or stored.decode("utf-8") != task_id_actual:
        print(f"Tarea cerrarConversacion {task_id_actual} no es la vigente para {celular}; abortando.")
        return

    print(f"Tarea cerrarConversacion iniciada con task_id: {task_id_actual} para el celular: {celular}")
    try:
        dbMySQLManager.actualizar_estado_conversacion(conversacion_id_mysql, 'completada')
        dbMongoManager.cerrar_conversacion(celular, conversacion_id_mongo)
    except Exception as e:
        print(f"Error en cerrarConversacion: {e}")
    finally:
        stored = get_scheduled_task_id(f"cerrar_{celular}")
        if stored and stored.decode("utf-8") == task_id_actual:
            clear_scheduled_task_id(f"cerrar_{celular}")

@celery.task(bind=True)
def enviar_respuesta(self, cliente_mysql, conversacion_id_mysql):
    task_id_actual = self.request.id
    celular = cliente_mysql["celular"]
    print(f"Tarea enviar_respuesta iniciada con task_id: {task_id_actual} para el celular: {celular}")
    nombre = cliente_mysql["nombre"]
    cliente_id_mysql = cliente_mysql["cliente_id"]
    motivo_actual=cliente_mysql['motivo']
    estado_actual = cliente_mysql['estado']
    conversacion_actual=dbMongoManager.obtener_conversacion_actual(celular)
    print("Enviando respuesta a:", celular)
    
    campanha_registro = dbMySQLManager.asociar_cliente_a_campana_mas_reciente(cliente_id_mysql)
    campanha = campanha_registro["descripcion"] if campanha_registro else ""
    
    dbMySQLManager.actualizar_fecha_ultima_interaccion(cliente_id_mysql, datetime.now(pytz.utc))

    print("Conversación actual:", conversacion_actual)
    
    max_intentos = 5
    intento_actual = 0
    try:
        while intento_actual < max_intentos:
            try:
                
                motivo = openai.clasificar_motivo(conversacion_actual)
                print("Intención detectada antes extraer json:", motivo)
                motivo = extraer_json(motivo)
                
                if motivo:
                    print("Motivo detectado:", motivo)
                    motivo_list = json_a_lista(motivo)
                    if not (motivo_list[0] in [1, 2, 3, 4, 5]):
                        raise ValueError("El motivo no está entre 1,2,3,4 o 5")
                    if not (motivo_list[1] in [1, 2, 3, 4]):
                        raise ValueError("El estado no está entre 1,2,3 o 4")

                    if motivo_list[0] == 4 and dbMySQLManager.hay_cita_pendiente(cliente_id_mysql):
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
                    
                    nuevo_motivo = name_motivo(motivo_list[0])
                    nuevo_estado = name_estado(motivo_list[1])
                    detalle = motivo_list[2]
                    guardar_motivo(motivo_actual, nuevo_motivo, cliente_id_mysql, motivo_list[1])
                    guardar_estado(estado_actual, nuevo_estado, cliente_id_mysql, "Cambio de estado: " + nuevo_estado)
                    response_message = openai.mensaje_personalizado(nombre,nuevo_motivo, nuevo_estado, detalle, conversacion_actual)
                    print("Response message json:", response_message)
                    twilio.send_message(celular, response_message)
                    dbMongoManager.guardar_respuesta_ultima_interaccion_chatbot(celular, response_message)
                    dbMySQLManager.actualizar_fecha_ultima_interaccion_bot(cliente_id_mysql, datetime.now(pytz.utc))
                    break  # Sale del while si todo sale bien
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
                    break
    finally:
        task_id_almacenado = get_scheduled_task_id(f"respuesta_{celular}")
        if task_id_almacenado and task_id_almacenado.decode("utf-8") == task_id_actual:
            clear_scheduled_task_id(f"respuesta_{celular}") 

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
            response_message = "¡Hola! Esta es la línea de reactivaciones y hemos observado que no tienes reactivaciones pendientes o no estás registrado en el sistema. Te invitamos a contactar al número +51953983765 para más información." 
            twilio.send_message(celular, response_message)
            return

        #Buscar al cliente
        cliente_mysql = dbMySQLManager.obtener_cliente_por_celular(celular)
        print("cliente_mysql:", cliente_mysql, type(cliente_mysql))
        if not cliente_mysql:
            response_message = "¡Hola! Esta es la línea de reactivaciones y hemos observado que no tienes reactivaciones pendientes o no estás registrado en el sistema. Te invitamos a contactar al número +51953983765 para más información." 
            twilio.send_message(celular, response_message)
            return 
        
        if cliente_mysql["nombre"].strip() == "":
            cliente_mysql["nombre"] = profileName
            dbMySQLManager.actualizar_nombre_cliente(cliente_mysql["cliente_id"], profileName)
        
        conversacion_activa_id=dbMongoManager.obtener_conversacion_actual_id(celular)
        if not conversacion_activa_id:
            # Se crea una conversacion activa, solo se crea
            print("Creando una nueva conversación activa para el cliente.")
            dbMongoManager.crear_conversacion_activa(celular)
            conversacion_activa_id=dbMongoManager.obtener_conversacion_actual_id(celular)
        
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

        lock_distribuido = acquire_lock_with_retry(celular, ttl=10000, max_wait=20, interval=0.1)
        if not lock_distribuido:
            print(f"No se pudo adquirir lock para {celular} tras esperar 20 segundos.")
            response_message = "Lo siento, hubo un problema al procesar tu mensaje. Inténtalo más tarde."
            twilio.send_message(celular, response_message)
            return 'OK', 200
        
        try:
            new_task_resp = enviar_respuesta.apply_async(
                args=[cliente_mysql, conversacion_id_mysql],
                countdown=18
            )
            new_task_cerr = cerrarConversacion.apply_async(
                args=[conversacion_id_mysql,conversacion_activa_id, celular],
                countdown=900
            )

            if not (set_scheduled_task_id(f"respuesta_{celular}", new_task_resp.id) and 
                    set_scheduled_task_id(f"cerrar_{celular}", new_task_cerr.id)):
                task_id_resp = get_scheduled_task_id(f"respuesta_{celular}")
                if task_id_resp:
                    print(f"Revocando tarea de respuesta {task_id_resp.decode('utf-8')} para {celular}")
                    revoke_task(task_id_resp.decode('utf-8'))
                    clear_scheduled_task_id(f"respuesta_{celular}")
                
                task_id_cerr = get_scheduled_task_id(f"cerrar_{celular}")
                if task_id_cerr:
                    print(f"Revocando tarea de cierre {task_id_cerr.decode('utf-8')} para {celular}")
                    revoke_task(task_id_cerr.decode('utf-8'))
                    clear_scheduled_task_id(f"cerrar_{celular}")
                
                # Intentar nuevamente establecer las claves:
                set_scheduled_task_id(f"respuesta_{celular}", new_task_resp.id)
                set_scheduled_task_id(f"cerrar_{celular}", new_task_cerr.id)
        
        finally:
            # Liberar el lock distribuido
            release_lock(lock_distribuido)
        
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


def name_estado(estado_num):
    if estado_num==1:
        return 'interesado'
    elif estado_num==2:
        return 'no interesado'
    elif estado_num==3:
        return 'promesa de pago'
    else:
        return 'en seguimiento'

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
