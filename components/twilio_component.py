from twilio.rest import Client
from api_keys.api_keys import account_sid, auth_token, messaging_service_sid

class TwilioManager:
    def __init__(self):
        self.client = self._authenticate()

    def _authenticate(self):
        return Client(account_sid, auth_token)

    def send_message(self, to_number, message_body):
        to_number = f'whatsapp:{to_number}' if not to_number.startswith('whatsapp:') else to_number

        message = self.client.messages.create(
            body=message_body,
            from_='whatsapp:+51944749102',  # Cambia por tu número de Twilio
            #from_='whatsapp:+14155238886',  # Cambia por tu número de Twilio
            to=to_number
        )
        print(f"Message sent to {to_number}: {message.sid}")
        message_status = self.client.messages(message.sid).fetch()
        print(f"Message status: {message_status.status}")
        return message.sid

    def send_template_message(self, to_number, template_content_sid, parameters):
        to_number = f'whatsapp:{to_number}' if not to_number.startswith('whatsapp:') else to_number
        
        # Configuración del mensaje usando Content SID
        message = self.client.messages.create(
            content_sid=template_content_sid,  # Aquí pones el Content SID de la plantilla
            from_='whatsapp:+51944749102',  # Número de Twilio
            #from_='whatsapp:+14155238886',
            to=to_number,
            content_variables=parameters  # Parámetros de la plantilla
        )
        print("message : ", message)
        print(f"Template message sent to {to_number}: {message.sid}")
        return message.sid