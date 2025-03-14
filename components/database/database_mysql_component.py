import mysql.connector
from mysql.connector import Error
from datetime import datetime
import pytz

class DataBaseMySQLManager:
    def __init__(self):
        self.connection = self._connect()

    def _reconnect_if_needed(self):
        """Reconnects if the current connection is not active."""
        if not self.connection.is_connected():
            print("Reconectando a MySQL...")
            self.connection = self._connect()    

    def _connect(self):
        try:
            connection = mysql.connector.connect(
                #host='localhost',
                #user='danielrp551',
                #database='chatbot_db',
                #password='26deJULIO@'
                host='chatbot-mysql.c5yiocg6aj0e.us-east-2.rds.amazonaws.com',
                database='bot_maqui_react',
                user='admin',
                password='zQumSnUd9MNtjcsK'
            )
            if connection.is_connected():
                print("Conectado a MySQL")
            return connection
        except Error as e:
            print(f"Error al conectar a MySQL: {e}")
            return None

    def obtener_id_cliente_por_celular(self, celular):
        self._reconnect_if_needed()
        """Obtiene el cliente_id usando el número de celular."""
        cursor = self.connection.cursor()
        query = "SELECT * FROM cliente WHERE celular=celular"
        cursor.execute(query, (celular,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    def obtener_cliente_por_celular(self, celular):
        self._reconnect_if_needed()
        """Obtiene el cliente_id usando el número de celular."""
        cursor = self.connection.cursor(dictionary=True)
        query = "SELECT * FROM cliente WHERE celular = %s"
        cursor.execute(query, (celular,))
        return cursor.fetchone()

    def existe_cliente_por_celular(self, celular):
        self._reconnect_if_needed()
        """Verifica si un cliente ya existe en la base de datos usando el número de celular."""
        return self.obtener_id_cliente_por_celular(celular) is not None

    def insertar_cliente(self, documento_identidad, tipo_documento,
                         nombre, apellido, celular, email,estado="en seguimiento"):
        self._reconnect_if_needed()
        """Inserta un nuevo cliente en la tabla de clientes si no existe ya."""
        if not self.existe_cliente_por_celular(celular):
            cursor = self.connection.cursor()
            query = """INSERT INTO clientes (documento_identidad, tipo_documento, nombre, apellido, celular, email,estado)
                       VALUES (%s, %s, %s, %s, %s, %s,%s)"""
            cursor.execute(query, (documento_identidad, tipo_documento, nombre, apellido, celular, email,estado))
            self.connection.commit()
            print("Cliente insertado en MySQL.")
            return cursor.lastrowid
        else:
            print("El cliente ya existe en MySQL.")
            return self.obtener_id_cliente_por_celular(celular)

    def obtener_cliente(self, cliente_id):
        self._reconnect_if_needed()
        """Obtiene los datos de un cliente por su ID."""
        cursor = self.connection.cursor(dictionary=True)
        query = "SELECT * FROM clientes WHERE cliente_id = %s"
        cursor.execute(query, (cliente_id,))
        return cursor.fetchone()

    def insertar_cita(self, cliente_id, fecha_cita, estado_cita="agendada", conversacion_id=None):
        self._reconnect_if_needed()
        """Inserta una nueva cita para un cliente en la tabla de citas."""
        cursor = self.connection.cursor()
        query = """INSERT INTO cita (cliente_id, fecha_cita, estado_cita, conversacion_id)
                   VALUES (%s, %s, %s, %s)"""
        cursor.execute(query, (cliente_id, fecha_cita, estado_cita, conversacion_id))
        self.connection.commit()
        return cursor.lastrowid

    def hay_cita_pendiente(self, cliente_id):
        self._reconnect_if_needed()
        """Verifica si un cliente tiene al menos una cita pendiente desde el momento actual en adelante."""
        cursor = self.connection.cursor(dictionary=True)
        query = "SELECT 1 FROM cita WHERE cliente_id = %s AND fecha_cita > NOW() AND estado_cita = 'pendiente' LIMIT 1"
        cursor.execute(query, (cliente_id,))
        return cursor.fetchone() is not None

    def obtener_citas_cliente(self, cliente_id):
        self._reconnect_if_needed()
        """Obtiene todas las citas de un cliente."""
        cursor = self.connection.cursor(dictionary=True)
        query = "SELECT * FROM cita WHERE cliente_id = %s"
        cursor.execute(query, (cliente_id,))
        return cursor.fetchall()
    
    def obtener_citas_por_estado(self, estado_cita):
        self._reconnect_if_needed()
        """Obtiene todas las citas en un estado específico."""
        cursor = self.connection.cursor(dictionary=True)
        query = "SELECT * FROM cita WHERE estado_cita = %s"
        cursor.execute(query, (estado_cita,))
        return cursor.fetchall()
    
    def obtener_citas_por_estado_con_numero(self, estado_cita):
        self._reconnect_if_needed()
        """Obtiene todas las citas en un estado específico junto con el celular del cliente asociado."""
        cursor = self.connection.cursor(dictionary=True)
        query = """        
            SELECT c.cita_id, c.fecha_cita, c.estado_cita, c.motivo, c.fecha_creacion, c.aviso, 
               cl.cliente_id, cl.nombre, cl.apellido, cl.celular
            FROM cita c
            JOIN cliente cl ON c.cliente_id = cl.cliente_id
            WHERE c.estado_cita = %s
            """
        cursor.execute(query, (estado_cita,))
        return cursor.fetchall()

    def insertar_conversacion(self, cliente_id, mensaje, resultado=None, estado_conversacion="activa"):
        self._reconnect_if_needed()
        """Inserta una nueva conversación para un cliente en la tabla de conversaciones."""
        cursor = self.connection.cursor()
        query = """INSERT INTO conversacion (cliente_id, mensaje, resultado, estado_conversacion, fecha_conversacion)
                   VALUES (%s, %s, %s, %s, %s)"""
        cursor.execute(query, (cliente_id, mensaje, resultado, estado_conversacion, datetime.now()))
        self.connection.commit()
        return cursor.lastrowid

    def obtener_conversaciones_cliente(self, cliente_id, estado_conversacion=None):
        self._reconnect_if_needed()
        """Obtiene todas las conversaciones de un cliente, filtrando opcionalmente por estado."""
        cursor = self.connection.cursor(dictionary=True)
        if estado_conversacion:
            query = "SELECT * FROM conversacion WHERE cliente_id = %s AND estado_conversacion = %s"
            cursor.execute(query, (cliente_id, estado_conversacion))
        else:
            query = "SELECT * FROM conversacion WHERE cliente_id = %s"
            cursor.execute(query, (cliente_id,))
        return cursor.fetchall()

    def actualizar_estado_conversacion(self, conversacion_id, nuevo_estado):
        self._reconnect_if_needed()
        """Actualiza el estado de una conversación a 'completada' o 'activa'."""
        cursor = self.connection.cursor()
        query = "UPDATE conversacion SET estado_conversacion = %s WHERE conversacion_id = %s"
        cursor.execute(query, (nuevo_estado, conversacion_id))
        self.connection.commit()

    def obtener_conversacion_activa(self, cliente_id):
        self._reconnect_if_needed()
        """Obtiene la conversación activa actual de un cliente, si existe."""
        cursor = self.connection.cursor(dictionary=True)
        query = "SELECT * FROM conversacion WHERE cliente_id = %s AND estado_conversacion = 'activa'"
        cursor.execute(query, (cliente_id,))
        return cursor.fetchone()



    '''
    def actualizar_estado_lead(self, lead_id, nuevo_estado):
        self._reconnect_if_needed()
        """Actualiza el estado de un lead en la tabla de leads."""
        cursor = self.connection.cursor()
        query = "UPDATE leads SET estado_lead = %s WHERE lead_id = %s"
        cursor.execute(query, (nuevo_estado, lead_id))
        self.connection.commit()
        print(f"Estado del lead {lead_id} actualizado a '{nuevo_estado}'.")    
    '''


    def actualizar_estado_cliente(self, client_id, nuevo_estado):
        self._reconnect_if_needed()
        cursor = self.connection.cursor()
        query = "UPDATE cliente SET estado = %s WHERE cliente_id = %s"
        cursor.execute(query,(nuevo_estado,client_id))
        self.connection.commit()
        print(f"Estado del cliente {client_id} actualizado a {nuevo_estado}.")

    def actualizar_motivo_cliente(self, client_id, nuevo_motivo):
        self._reconnect_if_needed()
        cursor = self.connection.cursor()
        query = "UPDATE cliente SET motivo = %s WHERE cliente_id = %s"
        cursor.execute(query,(nuevo_motivo,client_id))
        self.connection.commit()
        print(f"Motivo del cliente {client_id} actualizado a {nuevo_motivo}.")
    

    '''
        def actualizar_estado_cliente_no_interes(self, client_id, nuevo_estado,categoria_no_interes,detalle_no_interes):
        self._reconnect_if_needed()
        cursor = self.connection.cursor()
        query = "UPDATE clientes SET estado = %s, categoria_no_interes = %s, detalle_no_interes = %s WHERE cliente_id = %s"
        cursor.execute(query,(nuevo_estado,categoria_no_interes,detalle_no_interes,client_id))
        self.connection.commit()
        print(f"Estado del cliente {client_id} actualizado a {nuevo_estado}.")  
    '''
      
    
    def actualizar_fecha_ultima_interaccion(self, cliente_id, fecha):
        self._reconnect_if_needed()
        cursor = self.connection.cursor()
        sql = "UPDATE cliente SET fecha_ultima_interaccion = %s WHERE cliente_id = %s"
        cursor.execute(sql, (fecha, cliente_id))

        # Actualiza la fecha en la conversación activa
        sql_conversacion = """
            UPDATE conversacion 
            SET fecha_ultima_interaccion = %s 
            WHERE cliente_id = %s AND estado_conversacion = 'activa'
        """
        cursor.execute(sql_conversacion, (fecha, cliente_id))

        self.connection.commit()
        cursor.close()

    def actualizar_fecha_ultima_interaccion_bot(self, cliente_id, fecha):
        self._reconnect_if_needed()
        cursor = self.connection.cursor()
        sql = "UPDATE cliente SET fecha_ultima_interaccion_bot = %s WHERE cliente_id = %s"
        cursor.execute(sql, (fecha, cliente_id))
        
        # Actualiza la fecha en la conversación activa
        sql_conversacion = """
            UPDATE conversacion 
            SET fecha_ultima_interaccion = %s 
            WHERE cliente_id = %s AND estado_conversacion = 'activa'
        """
        cursor.execute(sql_conversacion, (fecha, cliente_id))    
        
        self.connection.commit()
        cursor.close()

    '''
    def obtener_citas_pendientes(self):
        self._reconnect_if_needed()
        cursor = self.connection.cursor(dictionary=True)
        sql = """
            SELECT c.*, p.estado_pago FROM cita c
            LEFT JOIN pago p ON c.cita_id = p.cita_id
            WHERE c.estado_cita = 'agendada' AND (p.estado_pago IS NULL OR p.estado_pago != 'completado')
        """
        cursor.execute(sql)
        citas = cursor.fetchall()
        cursor.close()
        return citas
    '''
    def obtener_todos_los_clientes(self):
        self._reconnect_if_needed()
        """Obtiene los datos de un cliente por su ID."""
        cursor = self.connection.cursor(dictionary=True)
        query = "SELECT * FROM cliente"
        cursor.execute(query)
        return cursor.fetchall()
    

    def obtener_citas_pasadas(self, fecha_actual):
        self._reconnect_if_needed()
        cursor = self.connection.cursor(dictionary=True)
        sql = """
            SELECT * FROM cita
            WHERE estado_cita = 'agendada' AND fecha_cita <= %s
        """
        cursor.execute(sql, (fecha_actual,))
        citas = cursor.fetchall()
        cursor.close()
        return citas
    

    def actualizar_estado_cita(self, cita_id, nuevo_estado):
        self._reconnect_if_needed()
        cursor = self.connection.cursor()
        sql = "UPDATE cita SET estado_cita = %s WHERE cita_id = %s"
        cursor.execute(sql, (nuevo_estado, cita_id))
        self.connection.commit()
        cursor.close()
    

    '''
    def actualizar_aviso_cita(self, cita_id, aviso):
        self._reconnect_if_needed()
        cursor = self.connection.cursor()
        sql = "UPDATE cita SET aviso = %s WHERE cita_id = %s"
        cursor.execute(sql, (aviso, cita_id))
        self.connection.commit()
        cursor.close()
    '''


    def obtener_estado_cliente(self, cliente_id):
        self._reconnect_if_needed()
        cursor = self.connection.cursor()
        sql = "SELECT estado FROM cliente WHERE cliente_id = %s"
        cursor.execute(sql, (cliente_id,))
        estado = cursor.fetchone()[0]
        cursor.close()
        return estado
    
    def actualizar_nombre_cliente(self, cliente_id, nombre):
        self._reconnect_if_needed()
        cursor = self.connection.cursor()
        sql = "UPDATE cliente SET nombre = %s WHERE cliente_id = %s"
        cursor.execute(sql, (nombre, cliente_id))
        self.connection.commit()
        cursor.close()


    def insertar_estado_historico_cliente(self, cliente_id, nuevo_estado, detalle):
        self._reconnect_if_needed()
        cursor = self.connection.cursor()

        # Verificar si ya existe un registro en el histórico para el cliente, obteniendo el último estado
        query_state = """
            SELECT estado
            FROM historico_estado 
            WHERE cliente_id = %s
            ORDER BY fecha_estado DESC 
            LIMIT 1
        """
        cursor.execute(query_state, (cliente_id,))
        result = cursor.fetchone()

        # Si no hay registro previo o el último estado es diferente al nuevo, insertar el nuevo estado
        if result is None or result[0] != nuevo_estado:
            query_insert = "INSERT INTO historico_estado (cliente_id, estado, fecha_estado, detalle) VALUES (%s, %s, %s, %s)"
            cursor.execute(query_insert, (cliente_id, nuevo_estado, datetime.now(), detalle))
            print(f"Estado '{nuevo_estado}' añadido al histórico para el cliente {cliente_id}.")

        self.connection.commit()
        cursor.close()

    def insertar_motivo_historico_cliente(self, cliente_id, nuevo_motivo, detalle):
        self._reconnect_if_needed()
        cursor = self.connection.cursor()

        # Verificar si ya existe un registro en el histórico para el cliente, obteniendo el último estado
        query_state = """
            SELECT motivo
            FROM historico_motivo
            WHERE cliente_id = %s
            ORDER BY fecha_cambio DESC 
            LIMIT 1
        """
        cursor.execute(query_state, (cliente_id,))
        result = cursor.fetchone()

        # Si no hay registro previo o el último estado es diferente al nuevo, insertar el nuevo estado
        if result is None or result[0] != nuevo_motivo:
            query_insert = "INSERT INTO historico_motivo (cliente_id, motivo, fecha_cambio, detalle) VALUES (%s, %s, %s, %s)"
            cursor.execute(query_insert, (cliente_id, nuevo_motivo, datetime.now(), detalle))
            print(f"Motivo '{nuevo_motivo}' añadido al histórico para el cliente {cliente_id}.")

        self.connection.commit()
        cursor.close()


    def obtener_cita_mas_cercana(self, cliente_id):
        """
        Obtiene la cita más cercana para un cliente en estado 'agendada'
        y cuya fecha_cita sea mayor que la fecha actual en la zona horaria de Lima.

        :param cliente_id: ID del cliente.
        :return: La cita más cercana en estado 'agendada' o None si no se encuentra ninguna.
        """
        try:
            # Configurar la zona horaria de Lima
            lima_tz = pytz.timezone("America/Lima")
            ahora = datetime.now(lima_tz)

            self._reconnect_if_needed()
            cursor = self.connection.cursor(dictionary=True)

            # Query para buscar la cita más cercana
            query = """
                SELECT * FROM cita
                WHERE cliente_id = %s AND estado_cita = 'agendada' AND fecha_cita > %s
                ORDER BY fecha_cita ASC
                LIMIT 1
            """
            cursor.execute(query, (cliente_id, ahora))
            cita = cursor.fetchone()
            cursor.close()

            if cita:
                print(f"Cita más cercana encontrada: {cita}")
            else:
                print("No se encontró ninguna cita agendada futura para este cliente.")

            return cita

        except Exception as e:
            print(f"Error al obtener la cita más cercana: {e}")
            return None
    
    def obtener_clientes_por_filtro(self, filtro):
        cursor = self.connection.cursor(dictionary=True)
        query = "SELECT * FROM cliente WHERE " + filtro
        cursor.execute(query)
        return cursor.fetchall()
    
    def asociar_cliente_a_campana_mas_reciente(self, cliente_id):
        """
        Asocia un cliente a la campanha más reciente que esté activa y devuelve los detalles de la campanha.

        Args:
            cliente_id (int): ID del cliente a asociar.

        Returns:
            dict: Detalles de la campanha asociada o None si no hay campanhas activas.
        """
        self._reconnect_if_needed()
        cursor = self.connection.cursor(dictionary=True)

        try:
            # Obtener la campanha activa más reciente
            query_campana = """
                SELECT * FROM campanha
                WHERE estado_campanha = 'activa'
                ORDER BY fecha_creacion DESC
                LIMIT 1
            """
            cursor.execute(query_campana)
            campana = cursor.fetchone()

            if not campana:
                print("No hay campanhas activas disponibles.")
                return None

            campana_id = campana['campanha_id']

            # Verificar si ya existe la asociación
            query_check = """
                SELECT * FROM cliente_campanha
                WHERE cliente_id = %s AND campanha_id = %s
            """
            cursor.execute(query_check, (cliente_id, campana_id))
            existe_asociacion = cursor.fetchone()

            if existe_asociacion:
                print("El cliente ya está asociado a la campanha más reciente.")
            else:
                # Insertar la asociación en la tabla intermedia
                query_insert = """
                    INSERT INTO cliente_campanha (cliente_id, campanha_id)
                    VALUES (%s, %s)
                """
                cursor.execute(query_insert, (cliente_id, campana_id))

                # Incrementar el num_clientes de la campanha
                query_update_num_clientes = """
                    UPDATE campanha
                    SET num_clientes = num_clientes + 1
                    WHERE campanha_id = %s
                """
                cursor.execute(query_update_num_clientes, (campana_id,))

                self.connection.commit()
                print(f"Cliente {cliente_id} asociado a la campanha {campana_id} y num_clientes incrementado.")

            return campana

        except Exception as e:
            print(f"Error al asociar cliente a la campanha: {e}")
            return None

        finally:
            cursor.close()

    def buscar_cita_por_fecha_cliente(self, cliente_id, fecha_cita):
        """
        Busca una cita agendada para un cliente en una fecha específica.
        """
        cursor = self.connection.cursor(dictionary=True)
        query = "SELECT * FROM cita WHERE cliente_id = %s AND fecha_cita = %s"
        cursor.execute(query, (cliente_id, fecha_cita))
        return cursor.fetchone()
    
    def obtener_clientes_filtrados(self, fecha_inicio=None, fecha_fin=None, estado=None, limite=None):
        """
        Obtiene clientes filtrados por fecha de creación, estado (simple o múltiple), bound y/o límite de registros.

        Args:
            fecha_inicio (str): Fecha inicial en formato 'YYYY-MM-DD'.
            fecha_fin (str): Fecha final en formato 'YYYY-MM-DD'.
            estado (str o list): 
                - Puede ser un string representando un único estado, 
                - O una lista de strings con múltiples estados, 
                - O None (no filtra por estado).
            limite (int): Límite de registros a devolver.
            bound (bool): Filtrar por si el cliente es bound (True o False).

        Returns:
            list: Lista de clientes que cumplen con los filtros.
        """
        self._reconnect_if_needed()
        cursor = self.connection.cursor(dictionary=True)

        # Construcción dinámica de la consulta
        query = "SELECT * FROM cliente WHERE 1=1"
        params = []

        # Filtro por fecha de creación (si se proporciona)
        if fecha_inicio:
            query += " AND fecha_creacion >= %s"
            params.append(fecha_inicio)
        if fecha_fin:
            query += " AND fecha_creacion <= %s"
            params.append(fecha_fin)

        # Filtro por estado (si se proporciona)
        if estado is not None:
            if isinstance(estado, list):
                # Estado es una lista de valores
                placeholders = ", ".join(["%s"] * len(estado))
                query += f" AND estado IN ({placeholders})"
                params.extend(estado)
            else:
                # Estado es un único valor (string)
                query += " AND estado = %s"
                params.append(estado)

        # Límite de registros (si se proporciona)
        if limite:
            query += " LIMIT %s"
            params.append(limite)

        # Ejecución de la consulta
        cursor.execute(query, tuple(params))
        resultados = cursor.fetchall()
        cursor.close()

        return resultados
    