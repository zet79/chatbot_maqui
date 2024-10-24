import os.path
import datetime as dt

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pytz

SCOPES = ["https://www.googleapis.com/auth/calendar"]

class GoogleCalendarManager:
    def __init__(self):
        self.service = self._authenticate()

    def _authenticate(self):
        creds = None

        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file("client_secret_app_escritorio_oauth.json", SCOPES)
                #creds = flow.run_local_server(port=0)
                flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
                auth_url, _ = flow.authorization_url(prompt='consent')
                # Imprime la URL de autenticación para abrirla en el navegador local
                print(f"Por favor, abre este enlace en tu navegador: {auth_url}")
                
                # Después de autenticarte, obtén el código de autorización
                code = input('Introduce el código de autorización: ')
                flow.fetch_token(code=code)
                creds = flow.credentials
            # Save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(creds.to_json())

        return build("calendar", "v3", credentials=creds)

    def list_upcoming_events(self, max_results=10):
        now = dt.datetime.utcnow().isoformat() + "Z"
        tomorrow = (dt.datetime.now() + dt.timedelta(days=5)).replace(hour=23, minute=59, second=0, microsecond=0).isoformat() + "Z"
        print("Parametros list upcoming events : ",now,tomorrow)
        events_result = self.service.events().list(
            calendarId='primary', timeMin=now, timeMax=tomorrow,
            maxResults=max_results, singleEvents=True,
            orderBy='startTime'
        ).execute()
        #print(events_result)
        events = events_result.get('items', [])

        if not events:
            print('No upcoming events found.')
        else:
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                print(start, event['summary'],event['id'])
        
        return events
    
    def listar_horarios_disponibles(self, max_results=10):
            # Definir horarios de trabajo
            working_hours = [
                {"start": dt.time(9, 0), "end": dt.time(13, 0)},   # De 9:00 AM a 1:00 PM
                {"start": dt.time(14, 0), "end": dt.time(19, 0)}   # De 2:00 PM a 7:00 PM
            ]
            
            # Configurar zona horaria de Lima
            lima_tz = pytz.timezone('America/Lima')

            # Obtener la hora actual y el final del rango de tiempo en Lima
            now = dt.datetime.now(lima_tz)
            end_of_week = (now + dt.timedelta(days=5)).replace(hour=23, minute=59, second=0, microsecond=0)

            print("Rango de tiempo para disponibilidad: ", now, end_of_week.isoformat())

            # Obtener eventos existentes en Google Calendar
            events_result = self.service.events().list(
                calendarId='primary', timeMin=now.isoformat(), timeMax=end_of_week.isoformat(),
                maxResults=max_results, singleEvents=True, orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])
            print("Eventos existentes: ", events)

            available_slots = []

            # Iterar sobre cada día de la semana para calcular los horarios disponibles
            for day_offset in range(6):  # Lunes a viernes (5 días)
                day = now + dt.timedelta(days=day_offset)
                if day.weekday() >= 5:  # Solo procesar de lunes a viernes
                    continue

                for hours in working_hours:
                    # Establecer el rango de trabajo para el día actual
                    start_time = lima_tz.localize(dt.datetime.combine(day.date(), hours["start"]))
                    end_time = lima_tz.localize(dt.datetime.combine(day.date(), hours["end"]))

                    # Restar los eventos ocupados dentro del horario de trabajo
                    for event in events:
                        event_start = dt.datetime.fromisoformat(event['start'].get('dateTime')).astimezone(lima_tz)
                        event_end = dt.datetime.fromisoformat(event['end'].get('dateTime')).astimezone(lima_tz)

                        # Si el evento interfiere con los horarios de trabajo
                        if start_time < event_end and event_start < end_time:
                            if event_start > start_time:
                                available_slots.append(f"{start_time.strftime('%Y-%m-%d %H:%M %p')} - {event_start.strftime('%Y-%m-%d %H:%M %p')}")
                            start_time = event_end

                    # Si quedan intervalos disponibles después de los eventos
                    if start_time < end_time:
                        available_slots.append(f"{start_time.strftime('%Y-%m-%d %H:%M %p')} - {end_time.strftime('%Y-%m-%d %H:%M %p')}")

            if not available_slots:
                print('No hay horarios disponibles.')
            else:
                print("Horarios disponibles: ", available_slots)

            return available_slots

    def create_event(self, summary, start_time, end_time, timezone, attendees=None):
        event = {
            'summary': summary,
            'start': {
                'dateTime': start_time,
                'timeZone': timezone,
            },
            'end': {
                'dateTime': end_time,
                'timeZone': timezone,
            }
        }

        if attendees:
            event["attendees"] = [{"email": email} for email in attendees]

        try:
            event = self.service.events().insert(calendarId="primary", body=event).execute()
            print(f"Event created: {event.get('htmlLink')}")
        except HttpError as error:
            print(f"An error has occurred: {error}")

    def update_event(self, event_id, summary=None, start_time=None, end_time=None):
        event = self.calendar_service.events().get(calendarId='primary', eventId=event_id).execute()

        if summary:
            event['summary'] = summary

        if start_time:
            event['start']['dateTime'] = start_time.strftime('%Y-%m-%dT%H:%M:%S')

        if end_time:
            event['end']['dateTime'] = end_time.strftime('%Y-%m-%dT%H:%M:%S')

        updated_event = self.calendar_service.events().update(
            calendarId='primary', eventId=event_id, body=event).execute()
        return updated_event

    def delete_event(self, event_id):
        self.calendar_service.events().delete(calendarId='primary', eventId=event_id).execute()
        return True
    
    def is_time_available(self, start_time, end_time):
        """
        Verifica si hay disponibilidad en Google Calendar entre el start_time y end_time.
        """
        time_min = (start_time + dt.timedelta(hours=5)).isoformat() + "Z"  # 'Z' indica UTC
        time_max = (end_time + + dt.timedelta(hours=5)).isoformat() + "Z"

        print("Parametros is_time_available : ",time_min,time_max)

        events_result = self.service.events().list(
            calendarId='primary', timeMin=time_min, timeMax=time_max,
            maxResults=10, singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        #print(events_result)
        print(events)

        # Si no hay eventos en el rango de tiempo, entonces está disponible
        return len(events) == 0

    

#calendar = GoogleCalendarManager()

#calendar.list_upcoming_events()

#calendar.create_event("Hola youtube","2023-08-08T16:30:00+02:00","2023-08-08T17:30:00+02:00","Europe/Madrid",["antonio@gmail.com","pedro@gmail.com"])