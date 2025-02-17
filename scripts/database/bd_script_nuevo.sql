DELIMITER ;

USE bot_maqui_react;

DROP TABLE IF EXISTS cliente_campanha;
DROP TABLE IF EXISTS accion_comercial;
DROP TABLE IF EXISTS pago;
DROP TABLE IF EXISTS cita;
DROP TABLE IF EXISTS conversacion;
DROP TABLE IF EXISTS historico_score;
DROP TABLE IF EXISTS historico_estado;
DROP TABLE IF EXISTS historico_motivo;
DROP TABLE IF EXISTS persona;
DROP TABLE IF EXISTS usuario;
DROP TABLE IF EXISTS leadh;
DROP TABLE IF EXISTS codigo_pago;
DROP TABLE IF EXISTS cliente;
DROP TABLE IF EXISTS campanha;
DROP TABLE IF EXISTS template;
DROP TABLE IF EXISTS rol;


-- Tabla de cliente
CREATE TABLE cliente (
  cliente_id int NOT NULL AUTO_INCREMENT,
  documento_identidad varchar(12) DEFAULT NULL,
  tipo_documento varchar(20) DEFAULT NULL,
  nombre varchar(100) NOT NULL,
  apellido varchar(100) DEFAULT NULL,
  celular varchar(20) NOT NULL,
  email varchar(100) DEFAULT NULL,
  fecha_creacion datetime DEFAULT CURRENT_TIMESTAMP,
  fecha_ultima_interaccion datetime DEFAULT NULL,
  fecha_ultima_interaccion_bot datetime DEFAULT NULL,
  estado varchar(25) DEFAULT 'en seguimiento',
  motivo varchar(25) DEFAULT 'desconocido',
  categoria_no_interes varchar(20) DEFAULT NULL,
  detalle_no_interes varchar(100) DEFAULT NULL,
  bound tinyint(1) DEFAULT NULL,
  observacion text,
  gestor varchar(100) DEFAULT '',
  accion varchar(50) DEFAULT '',
  in_out tinyint(1) DEFAULT '0',
  score varchar(20) NOT NULL DEFAULT 'no_score',
  PRIMARY KEY (cliente_id),
  UNIQUE KEY email (email)
);
-- Actualizar los clientes con bound en true a los prexistentes
-- UPDATE clientes SET bound = true WHERE bound IS NULL;
-- UPDATE clientes SET observaciones = "";

-- Tabla de lead
CREATE TABLE leadh (
  leadh_id int NOT NULL AUTO_INCREMENT,
  cliente_id int NOT NULL,
  fecha_contacto datetime NOT NULL,
  prioridad_lead int NOT NULL,
  leadh_source varchar(100) NOT NULL,
  campanha varchar(100) DEFAULT NULL,
  tipo varchar(100) DEFAULT NULL,
  canal_lead varchar(20) DEFAULT NULL,
  estado_lead varchar(25) DEFAULT 'en seguimiento',
  nota text,
  PRIMARY KEY (leadh_id),
  KEY cliente_id (cliente_id),
  CONSTRAINT leadh_ibfk_1 FOREIGN KEY (cliente_id) REFERENCES cliente (cliente_id) ON DELETE CASCADE
);



-- Tabla de conversacion
CREATE TABLE conversacion (
  conversacion_id int NOT NULL AUTO_INCREMENT,
  cliente_id int NOT NULL,
  fecha_conversacion datetime DEFAULT CURRENT_TIMESTAMP,
  tipo_conversacion varchar(50) DEFAULT NULL,
  mensaje text,
  resultado varchar(50) DEFAULT NULL,
  estado_conversacion varchar(25) DEFAULT 'activa',
  fecha_ultima_interaccion datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (conversacion_id),
  KEY cliente_id (cliente_id),
  CONSTRAINT conversacion_ibfk_1 FOREIGN KEY (cliente_id) REFERENCES cliente (cliente_id) ON DELETE CASCADE
);


-- Tabla de citas
-- Tabla de cita
CREATE TABLE cita (
  cita_id int NOT NULL AUTO_INCREMENT,
  cliente_id int NOT NULL,
  conversacion_id int DEFAULT NULL,
  fecha_cita datetime NOT NULL,
  estado_cita varchar(25) DEFAULT 'agendada',
  motivo varchar(100) NOT NULL,
  fecha_creacion datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  aviso int DEFAULT '0',
  PRIMARY KEY (cita_id),
  KEY cliente_id (cliente_id),
  KEY conversacion_id (conversacion_id),
  CONSTRAINT cita_ibfk_1 FOREIGN KEY (cliente_id) REFERENCES cliente (cliente_id) ON DELETE CASCADE,
  CONSTRAINT cita_ibfk_2 FOREIGN KEY (conversacion_id) REFERENCES conversacion (conversacion_id) ON DELETE SET NULL
);

-- UPDATE citas SET aviso = 0 WHERE aviso IS NULL;

-- Actualizar las citas preexistentes para que fecha_creacion sea igual a fecha_cita
-- UPDATE citas SET fecha_creacion = fecha_cita WHERE fecha_creacion IS NULL;

-- Tabla de pago
CREATE TABLE pago (
  pago_id int NOT NULL AUTO_INCREMENT,
  cliente_id int NOT NULL,
  cita_id int DEFAULT NULL,
  fecha_pago datetime NOT NULL,
  monto decimal(10,2) NOT NULL,
  metodo_pago varchar(50) NOT NULL,
  estado_pago varchar(25) DEFAULT 'pendiente',
  first_name varchar(40) DEFAULT '',
  last_name varchar(40) DEFAULT '',
  num_operacion varchar(40) DEFAULT '',
  PRIMARY KEY (pago_id),
  KEY cliente_id (cliente_id),
  KEY cita_id (cita_id),
  CONSTRAINT pago_ibfk_1 FOREIGN KEY (cliente_id) REFERENCES cliente (cliente_id) ON DELETE CASCADE,
  CONSTRAINT pago_ibfk_2 FOREIGN KEY (cita_id) REFERENCES cita (cita_id) ON DELETE SET NULL
);


CREATE TABLE historico_estado (
  historico_estado_id int NOT NULL AUTO_INCREMENT,
  cliente_id int NOT NULL,
  estado varchar(25) NOT NULL,
  fecha_estado datetime DEFAULT CURRENT_TIMESTAMP,
  detalle text NULL,
  PRIMARY KEY (historico_estado_id),
  KEY cliente_id (cliente_id),
  CONSTRAINT historico_estado_ibfk_1 FOREIGN KEY (cliente_id) REFERENCES cliente (cliente_id) ON DELETE CASCADE
);

CREATE TABLE historico_score (
  historico_score_id int NOT NULL AUTO_INCREMENT,
  cliente_id int NOT NULL,
  score varchar(20) NOT NULL,
  fecha_cambio datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (historico_score_id),
  KEY cliente_id (cliente_id),
  CONSTRAINT historico_score_ibfk_1 FOREIGN KEY (cliente_id) REFERENCES cliente (cliente_id) ON DELETE CASCADE
);

CREATE TABLE historico_motivo (
  historico_motivo_id int NOT NULL AUTO_INCREMENT,
  cliente_id int NOT NULL,
  motivo varchar(20) NOT NULL,
  fecha_cambio datetime DEFAULT CURRENT_TIMESTAMP,
  detalle text NULL,
  PRIMARY KEY (historico_motivo_id),
  KEY cliente_id (cliente_id),
  CONSTRAINT historico_motivo_ibfk_1 FOREIGN KEY (cliente_id) REFERENCES cliente (cliente_id) ON DELETE CASCADE
);


-- Tabla de rol
CREATE TABLE rol (
  rol_id int NOT NULL AUTO_INCREMENT,
  nombre_rol varchar(50) NOT NULL,
  descripcion varchar(255) DEFAULT NULL,
  PRIMARY KEY (rol_id),
  UNIQUE KEY nombre_rol (nombre_rol)
);

-- Tabla de usuario
CREATE TABLE usuario (
  usuario_id int NOT NULL AUTO_INCREMENT,
  username varchar(50) NOT NULL UNIQUE,
  password varchar(255) NOT NULL,
  rol_id int DEFAULT '2',
  activo int NOT NULL DEFAULT '1',
  PRIMARY KEY (usuario_id),
  FOREIGN KEY (rol_id) REFERENCES rol (rol_id) ON DELETE SET NULL
);

-- Tabla de persona
CREATE TABLE persona (
  persona_id int NOT NULL,
  nombre varchar(120) NOT NULL,
  primer_apellido varchar(120) NOT NULL,
  segundo_apellido varchar(120) DEFAULT NULL,
  celular varchar(12) DEFAULT NULL,
  num_leads int DEFAULT '0',
  PRIMARY KEY (persona_id),
  FOREIGN KEY (persona_id) REFERENCES usuario (usuario_id) ON DELETE CASCADE
);
-- tabla acciones comerciales -> cliente, asesor, accion
-- Tabla de accion_comercial
CREATE TABLE accion_comercial (
  accion_comercial_id int NOT NULL AUTO_INCREMENT,
  cliente_id int DEFAULT NULL,
  cita_id int DEFAULT NULL,
  pago_id int DEFAULT NULL,
  persona_id int DEFAULT NULL,
  nota text NOT NULL,
  PRIMARY KEY (accion_comercial_id),
  KEY cliente_id (cliente_id),
  KEY cita_id (cita_id),
  KEY pago_id (pago_id),
  KEY persona_id (persona_id),
  CONSTRAINT accion_comercial_ibfk_1 FOREIGN KEY (cliente_id) REFERENCES cliente (cliente_id) ON DELETE CASCADE,
  CONSTRAINT accion_comercial_ibfk_2 FOREIGN KEY (cita_id) REFERENCES cita (cita_id) ON DELETE SET NULL,
  CONSTRAINT accion_comercial_ibfk_3 FOREIGN KEY (pago_id) REFERENCES pago (pago_id) ON DELETE SET NULL,
  CONSTRAINT accion_comercial_ibfk_4 FOREIGN KEY (persona_id) REFERENCES persona (persona_id) ON DELETE SET NULL
);

-- Tabla de template
CREATE TABLE template (
  id int NOT NULL AUTO_INCREMENT,
  nombre_template varchar(100) NOT NULL,
  mensaje text NOT NULL,
  created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  template_content_sid varchar(120) NOT NULL DEFAULT '',
  parametro tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (id)
);

-- Tabla de campañas
CREATE TABLE campanha (
  campanha_id int NOT NULL AUTO_INCREMENT,
  nombre_campanha varchar(100) NOT NULL,
  descripcion text,
  fecha_creacion datetime DEFAULT CURRENT_TIMESTAMP,
  estado_campanha varchar(25) DEFAULT 'activa',
  mensaje_cliente text NULL,
  fecha_inicio datetime DEFAULT CURRENT_TIMESTAMP,
  fecha_fin datetime DEFAULT NULL,
  num_clientes int DEFAULT '0',
  tipo varchar(10) NOT NULL DEFAULT 'in',
  template_id int DEFAULT NULL,
  PRIMARY KEY (campanha_id),
  KEY fk_campana_template (template_id),
  CONSTRAINT fk_campanha_template FOREIGN KEY (template_id) REFERENCES template (id) ON DELETE SET NULL ON UPDATE CASCADE
);


-- Tabla intermedia para relación muchos a muchos
CREATE TABLE cliente_campanha (
  cliente_campanha_id int NOT NULL AUTO_INCREMENT,
  cliente_id int NOT NULL,
  campanha_id int NOT NULL,
  fecha_asociacion datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (cliente_campanha_id),
  KEY cliente_id (cliente_id),
  KEY campanha_id (campanha_id),
  CONSTRAINT cliente_campanha_ibfk_1 FOREIGN KEY (cliente_id) REFERENCES cliente (cliente_id) ON DELETE CASCADE,
  CONSTRAINT cliente_campanha_ibfk_2 FOREIGN KEY (campanha_id) REFERENCES campanha (campanha_id) ON DELETE CASCADE
);




-- Tabla de codigos de pago  (Bot Daniel)
CREATE TABLE codigo_pago (
	id_codigo_pago INT PRIMARY KEY AUTO_INCREMENT,
    cliente_id INT, -- clave foranea para vincularlo con la tabla cliente
    codigo INT UNIQUE NOT NULL, -- codigo de pago
    tipo_codigo VARCHAR(50), -- recaudacion, extranet o especial
    caso_relacionado VARCHAR(100), -- indica a qué caso está relacionado este código, por ejemplo se usará para 1 o más contratos, adjudicado no adjudicado etc.
    fecha_asignacion DATE NOT NULL, -- fecha en la que se asigno el código
    fecha_vencimiento DATE, -- fecha de vencimiento del codigo (puede ser null)
    activo BOOLEAN DEFAULT TRUE, -- indica si el código está activo (tambien se puede saber esto manualmente por la fecha de vencimiento y fecha actual)
    pago_realizado BOOLEAN DEFAULT FALSE, -- indica si el pago asociado al codigo se realizó por el cliente o todavia no , SE PODRÍA ELIMINAR ESTE CAMPO
    FOREIGN KEY (cliente_id) REFERENCES cliente (cliente_id) ON DELETE CASCADE
);





