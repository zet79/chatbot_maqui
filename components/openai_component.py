import openai
from api_keys.api_keys import openai_api_key

class OpenAIManager:
    def __init__(self):
        openai.api_key = openai_api_key

    def consult_product(self, user_question, conversation_history):
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un asistente virtual especializado en trasplantes capilares."},
                {"role": "user", "content": conversation_history + f"\nUser: {user_question}"}
            ],
            max_tokens=100,
        )
        return response.choices[0].message.content.strip()

    def clasificar_intencion(self, mensaje, conversation_history):
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": 
                    """
                    Eres un asistente virtual especializado en tratamientos capilares y trasplantes. 
                    Identifica la intención del usuario en base a las siguientes categorías:
                    - agendar una cita sin fecha
                    - agendar una cita con fecha
                    - hacer una consulta
                    - otros
                    """
                 },
                {"role": "user", "content": conversation_history + f"\nUser: {mensaje}"}
            ]
        )
        return response.choices[0].message.content.strip()

    def extract_datetime(self, message):
        # Aquí deberías implementar la lógica para extraer la fecha y hora de un mensaje
        # Ejemplo básico:
        date_str = "2024-10-25"
        time_str = "10:00"
        return date_str, time_str
