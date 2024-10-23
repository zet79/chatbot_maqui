import pandas as pd

# Leer el archivo Excel
def leer_datos_excel():
    df = pd.read_excel('clientes.xlsx')
    return df


def iniciar_conversacion():
    df = leer_datos_excel()  # Leer datos desde el Excel

    for index, row in df.iterrows():
        nombre = row['Nombre']
        apellido = row['Apellido']
        celular = row['Celular']

        # Crear mensaje personalizado
        mensaje = f"Hola {nombre} {apellido}, soy tu asistente virtual de Trasplante Capilar. ¿En qué puedo ayudarte hoy?"

        # Enviar mensaje usando Twilio
        client.messages.create(
            body=mensaje,
            from_='whatsapp:+14155238886',  # El número de Twilio (asegúrate de que esté configurado)
            to=f'whatsapp:+{celular}'  # Enviar al número de celular extraído
        )

        print(f"Mensaje enviado a {nombre} {apellido} al número {celular}")
