from openai import OpenAI
from api_keys.api_keys import openai_api_key
from prompt.prompt import prompt_intenciones, prompt_consulta_v2, prompt_lead_estado, prompt_cliente_nombre, prompt_consulta_v3, prompt_lead_estado_zoho, prompt_intencionesv2,prompt_consulta_v4
from helpers.helpers import formatear_conversacion, formatear_historial_conversaciones, formatear_horarios_disponibles
import pytz
from datetime import datetime

class OpenAIManager:
    def __init__(self):
        self.client = OpenAI(api_key=openai_api_key)

    def consulta(self, cliente,conversation_actual, conversation_history):
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt_consulta_v4(cliente) + formatear_conversacion(conversation_actual)},
            ],
            max_tokens=250,
        )
        return response.choices[0].message.content.strip()

    def clasificar_intencion(self, conversation_actual, conversation_history):
        conversacion_actual_formateada = formatear_conversacion(conversation_actual)
        #conversacion_history_formateada = formatear_historial_conversaciones(conversation_history)
        print("Fecha actual",datetime.now(pytz.timezone("America/Lima")).strftime("%Y-%m-%d"))
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt_intencionesv2(datetime.now(pytz.timezone("America/Lima")).strftime("%Y-%m-%d")) + conversacion_actual_formateada},
                #{"role": "user", "content": conversacion_actual_formateada}
            ],
            max_tokens=50,
        )
        #print("Conversación actual formateada:", conversacion_actual_formateada)
        print("Prompt intenciones:", prompt_intenciones(datetime.now(pytz.timezone("America/Lima")).strftime("%Y-%m-%d")) + conversacion_actual_formateada)
        return response.choices[0].message.content.strip()

    def consultaHorarios(self,cliente_mysql, horarios_disponibles, conversation_actual, conversation_history, fecha):
        horarios_disponibles = formatear_horarios_disponibles(horarios_disponibles)
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt_consulta_v4(cliente_mysql) + formatear_conversacion(conversation_actual)
                    + f"\n Los horarios disponibles para que le digas al cliente son {horarios_disponibles}"},
            ],
            max_tokens=100,
        )
        return response.choices[0].message.content.strip()

    def consultaCitareservada(self,cliente_mysql, reserva_cita, conversation_actual, conversation_history):
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt_consulta_v4(cliente_mysql) + formatear_conversacion(conversation_actual)
                    + "\n Dile que la cita ha sido reservada para el "},
            ],
            max_tokens=100,
        )
        return response.choices[0].message.content.strip()
    
    def consultaPago(self, cliente_mysql,link_pago, conversation_actual, conversation_history):
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt_consulta_v4(cliente_mysql) + formatear_conversacion(conversation_actual)
                    + f"\n Este es el link de pago que le digas :  {link_pago}"},
            ],
            max_tokens=100,
        )
        return response.choices[0].message.content.strip()

    def consultaLead(self, lead):
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt_lead_estado(lead) },
            ],
            max_tokens=100,
        )
        print("Prompt lead :", prompt_lead_estado(lead))
        return response.choices[0].message.content.strip()
    
    def consultaLeadZoho(self, lead):
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt_lead_estado_zoho(lead) },
            ],
            max_tokens=100,
        )
        #print("Prompt lead :", prompt_lead_estado_zoho(lead))
        return response.choices[0].message.content.strip()
    
    def consultaNombre(self, cliente, response_message,conversation_actual):
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt_cliente_nombre(cliente, response_message,formatear_conversacion(conversation_actual))},
            ],
            max_tokens=100,
        )
        return response.choices[0].message.content.strip()

    def extract_datetime(self, message):
        # Aquí deberías implementar la lógica para extraer la fecha y hora de un mensaje
        # Ejemplo básico:
        date_str = "2024-10-25"
        time_str = "10:00"
        return date_str, time_str
