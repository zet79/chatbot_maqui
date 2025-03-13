from datetime import datetime, timedelta
import pytz
from google.cloud import firestore

class DataBaseFirestoreManager:
    def __init__(self):
        self.db = self._connect()
        self.tz = pytz.timezone("America/Lima")
    
    def _connect(self):
        try:
            db = firestore.Client(database="(default)")
            print("Conexión exitosa a Firestore")
            return db
        except Exception as e:
            print(f"ERROR al conectar con Firestore: {e}")
            return None

    def crear_documento(self, celular, id_cliente, id_bot, mensaje, sender):
        data = {
            "celular": celular,
            "fecha": firestore.SERVER_TIMESTAMP, 
            "id_cliente": id_cliente,
            "id_bot": id_bot,
            "mensaje": mensaje,
            "sender": sender
        }
        try:
            doc_ref = self.db.collection("clientes").document() 
            doc_ref.set(data)
            print("Documento creado exitosamente.")
        except Exception as e:
            print(f"Error al crear el documento: {e}")

    def recuperar_mensajes_hoy(self, id_bot, celular):
        """
        Recupera todos los documentos (mensajes) de hoy para un cliente (usando el celular) y un bot específico.
        """
        try:
            now = datetime.now(self.tz)
            start_datetime = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_datetime = start_datetime + timedelta(days=1)

            query = (self.db.collection("clientes")
                     .where("id_bot", "==", id_bot)
                     .where("celular", "==", celular)
                     .where("fecha", ">=", start_datetime)
                     .where("fecha", "<", end_datetime))
            
            docs = query.stream()
            mensajes = [doc.to_dict() for doc in docs]
            return mensajes
        
        except Exception as e:
            print(f"Error al recuperar mensajes de hoy: {e}")
            return []
