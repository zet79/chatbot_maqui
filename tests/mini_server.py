from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from components.twilio_component import TwilioManager
from components.database.database_mongodb_component import DataBaseMongoDBManager
from components.database.database_mysql_component import DataBaseMySQLManager
from datetime import datetime
from pymongo import MongoClient
from components.openai_component import OpenAIManager

twilio_manager = TwilioManager()
dbMongoManager = DataBaseMongoDBManager()
dbMySQLManager = DataBaseMySQLManager()
openai = OpenAIManager()

app = Flask(__name__)

@app.route('/whatsapp', methods=['POST'])
def whatsapp():
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
    print("Nombre de perfil:", profileName)
    # Obtener cliente de la base de datos
    cliente = dbMongoManager.obtener_cliente_por_celular(celular)
    cliente_nuevo = False
    if not cliente:
        cliente = dbMongoManager.crear_cliente(nombre="",celular=celular)
        print("Cliente creado:", cliente)
    
    
    print("Cliente encontrado en la base de datos:", cliente["nombre"])

    if not dbMongoManager.hay_conversacion_activa(celular):
        # Se crea una conversacion activa, solo se crea
        print("Creando una nueva conversación activa para el cliente.")
        dbMongoManager.crear_conversacion_activa(celular)
    
    dbMongoManager.crear_nueva_interaccion(celular, incoming_msg)
    print("Interacción del cliente guardada en la conversación actual.") 

    conversation_actual = dbMongoManager.obtener_conversacion_actual(cliente["celular"])
    # = dbMongoManager.obtener_historial_conversaciones(cliente["celular"]) esto no va

    print("Conversación actual:", conversation_actual)

    motivo = openai.clasificar_motivo(conversation_actual)

    print('\n'+motivo+'\n')

    resp = MessagingResponse()
    resp.message("¡Mensaje recibido correctamente!")
    return "", 200



if __name__ == '__main__':
    app.run(debug=True, port=5000)