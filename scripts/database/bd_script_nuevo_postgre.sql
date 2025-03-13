SET search_path TO reactivaciones;

DROP TABLE IF EXISTS cliente_campanha CASCADE;
DROP TABLE IF EXISTS accion_comercial CASCADE;
DROP TABLE IF EXISTS pago CASCADE;
DROP TABLE IF EXISTS cita CASCADE;
DROP TABLE IF EXISTS conversacion CASCADE;
DROP TABLE IF EXISTS historico_score CASCADE;
DROP TABLE IF EXISTS historico_estado CASCADE;
DROP TABLE IF EXISTS historico_motivo CASCADE;
DROP TABLE IF EXISTS persona CASCADE;
DROP TABLE IF EXISTS usuario CASCADE;
DROP TABLE IF EXISTS leadh CASCADE;
DROP TABLE IF EXISTS codigo_pago CASCADE;
DROP TABLE IF EXISTS cliente CASCADE;
DROP TABLE IF EXISTS campanha CASCADE;
DROP TABLE IF EXISTS template CASCADE;
DROP TABLE IF EXISTS rol CASCADE;

-- Tabla de cliente
CREATE TABLE cliente (
  cliente_id SERIAL PRIMARY KEY,
  documento_identidad VARCHAR(12),
  tipo_documento VARCHAR(20),
  nombre VARCHAR(100) NOT NULL,
  apellido VARCHAR(100),
  celular VARCHAR(20) NOT NULL,
  email VARCHAR(100) UNIQUE,
  fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  fecha_ultima_interaccion TIMESTAMP,
  fecha_ultima_interaccion_bot TIMESTAMP,
  estado VARCHAR(25) DEFAULT 'en seguimiento',
  motivo VARCHAR(25) DEFAULT 'desconocido',
  categoria_no_interes VARCHAR(20),
  detalle_no_interes VARCHAR(100),
  bound BOOLEAN DEFAULT NULL,
  observacion TEXT,
  gestor VARCHAR(100) DEFAULT '',
  accion VARCHAR(50) DEFAULT '',
  in_out BOOLEAN DEFAULT FALSE,
  score VARCHAR(20) NOT NULL DEFAULT 'no_score'
);

-- Tabla de lead
CREATE TABLE leadh (
  leadh_id SERIAL PRIMARY KEY,
  cliente_id INT NOT NULL,
  fecha_contacto TIMESTAMP NOT NULL,
  prioridad_lead INT NOT NULL,
  leadh_source VARCHAR(100) NOT NULL,
  campanha VARCHAR(100),
  tipo VARCHAR(100),
  canal_lead VARCHAR(20),
  estado_lead VARCHAR(25) DEFAULT 'en seguimiento',
  nota TEXT,
  CONSTRAINT leadh_ibfk_1 FOREIGN KEY (cliente_id) REFERENCES cliente (cliente_id) ON DELETE CASCADE
);

-- Tabla de conversación
CREATE TABLE conversacion (
  conversacion_id SERIAL PRIMARY KEY,
  cliente_id INT NOT NULL,
  fecha_conversacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  tipo_conversacion VARCHAR(50),
  mensaje TEXT,
  resultado VARCHAR(50),
  estado_conversacion VARCHAR(25) DEFAULT 'activa',
  fecha_ultima_interaccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  nivel_satisfaccion VARCHAR(25),
  CONSTRAINT conversacion_ibfk_1 FOREIGN KEY (cliente_id) REFERENCES cliente (cliente_id) ON DELETE CASCADE
);

-- Tabla de cita
CREATE TABLE cita (
  cita_id SERIAL PRIMARY KEY,
  cliente_id INT NOT NULL,
  conversacion_id INT,
  fecha_cita TIMESTAMP NOT NULL,
  estado_cita VARCHAR(25) DEFAULT 'agendada',
  motivo VARCHAR(100) NOT NULL,
  fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  aviso BOOLEAN DEFAULT FALSE,
  CONSTRAINT cita_ibfk_1 FOREIGN KEY (cliente_id) REFERENCES cliente (cliente_id) ON DELETE CASCADE,
  CONSTRAINT cita_ibfk_2 FOREIGN KEY (conversacion_id) REFERENCES conversacion (conversacion_id) ON DELETE SET NULL
);

-- Tabla de pago
CREATE TABLE pago (
  pago_id SERIAL PRIMARY KEY,
  cliente_id INT NOT NULL,
  cita_id INT,
  fecha_pago TIMESTAMP NOT NULL,
  monto DECIMAL(10,2) NOT NULL,
  metodo_pago VARCHAR(50) NOT NULL,
  estado_pago VARCHAR(25) DEFAULT 'pendiente',
  first_name VARCHAR(40) DEFAULT '',
  last_name VARCHAR(40) DEFAULT '',
  num_operacion VARCHAR(40) DEFAULT '',
  CONSTRAINT pago_ibfk_1 FOREIGN KEY (cliente_id) REFERENCES cliente (cliente_id) ON DELETE CASCADE,
  CONSTRAINT pago_ibfk_2 FOREIGN KEY (cita_id) REFERENCES cita (cita_id) ON DELETE SET NULL
);

-- Tabla de historico_estado
CREATE TABLE historico_estado (
  historico_estado_id SERIAL PRIMARY KEY,
  cliente_id INT NOT NULL,
  estado VARCHAR(25) NOT NULL,
  fecha_estado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  detalle TEXT,
  CONSTRAINT historico_estado_ibfk_1 FOREIGN KEY (cliente_id) REFERENCES cliente (cliente_id) ON DELETE CASCADE
);

-- Tabla de historico_score
CREATE TABLE historico_score (
  historico_score_id SERIAL PRIMARY KEY,
  cliente_id INT NOT NULL,
  score VARCHAR(20) NOT NULL,
  fecha_cambio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT historico_score_ibfk_1 FOREIGN KEY (cliente_id) REFERENCES cliente (cliente_id) ON DELETE CASCADE
);

-- Tabla de historico_motivo
CREATE TABLE historico_motivo (
  historico_motivo_id SERIAL PRIMARY KEY,
  cliente_id INT NOT NULL,
  motivo VARCHAR(20) NOT NULL,
  fecha_cambio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  detalle TEXT,
  CONSTRAINT historico_motivo_ibfk_1 FOREIGN KEY (cliente_id) REFERENCES cliente (cliente_id) ON DELETE CASCADE
);

-- Tabla de rol
CREATE TABLE rol (
  rol_id SERIAL PRIMARY KEY,
  nombre_rol VARCHAR(50) NOT NULL UNIQUE,
  descripcion VARCHAR(255)
);

-- Tabla de usuario
CREATE TABLE usuario (
  usuario_id SERIAL PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  rol_id INT DEFAULT 2,
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  CONSTRAINT usuario_fk_rol FOREIGN KEY (rol_id) REFERENCES rol (rol_id) ON DELETE SET NULL
);

-- Tabla de persona
CREATE TABLE persona (
  persona_id INT PRIMARY KEY,
  nombre VARCHAR(120) NOT NULL,
  primer_apellido VARCHAR(120) NOT NULL,
  segundo_apellido VARCHAR(120),
  celular VARCHAR(12),
  num_leads INT DEFAULT 0,
  CONSTRAINT persona_fk_usuario FOREIGN KEY (persona_id) REFERENCES usuario (usuario_id) ON DELETE CASCADE
);

-- Tabla de accion_comercial
CREATE TABLE accion_comercial (
  accion_comercial_id SERIAL PRIMARY KEY,
  cliente_id INT,
  cita_id INT,
  pago_id INT,
  persona_id INT,
  estado VARCHAR(25),
  fecha_accion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  nota TEXT NOT NULL,
  CONSTRAINT accion_comercial_ibfk_1 FOREIGN KEY (cliente_id) REFERENCES cliente (cliente_id) ON DELETE CASCADE,
  CONSTRAINT accion_comercial_ibfk_2 FOREIGN KEY (cita_id) REFERENCES cita (cita_id) ON DELETE SET NULL,
  CONSTRAINT accion_comercial_ibfk_3 FOREIGN KEY (pago_id) REFERENCES pago (pago_id) ON DELETE SET NULL,
  CONSTRAINT accion_comercial_ibfk_4 FOREIGN KEY (persona_id) REFERENCES persona (persona_id) ON DELETE SET NULL
);

-- Tabla de template
CREATE TABLE template (
  id SERIAL PRIMARY KEY,
  nombre_template VARCHAR(100) NOT NULL,
  mensaje TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  template_content_sid VARCHAR(120) NOT NULL DEFAULT '',
  parametro BOOLEAN NOT NULL DEFAULT FALSE
);

-- Tabla de campanhas
CREATE TABLE campanha (
  campanha_id SERIAL PRIMARY KEY,
  nombre_campanha VARCHAR(100) NOT NULL,
  descripcion TEXT,
  fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  estado_campanha VARCHAR(25) DEFAULT 'activa',
  mensaje_cliente TEXT,
  fecha_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  fecha_fin TIMESTAMP,
  num_clientes INT DEFAULT 0,
  tipo VARCHAR(10) NOT NULL DEFAULT 'in',
  template_id INT,
  CONSTRAINT fk_campanha_template FOREIGN KEY (template_id) REFERENCES template (id) ON DELETE SET NULL ON UPDATE CASCADE
);

-- Tabla intermedia para relación muchos a muchos: cliente_campanha
CREATE TABLE cliente_campanha (
  cliente_campanha_id SERIAL PRIMARY KEY,
  cliente_id INT NOT NULL,
  campanha_id INT NOT NULL,
  fecha_asociacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT cliente_campanha_ibfk_1 FOREIGN KEY (cliente_id) REFERENCES cliente (cliente_id) ON DELETE CASCADE,
  CONSTRAINT cliente_campanha_ibfk_2 FOREIGN KEY (campanha_id) REFERENCES campanha (campanha_id) ON DELETE CASCADE
);

-- Tabla de códigos de pago
CREATE TABLE codigo_pago (
  id_codigo_pago SERIAL PRIMARY KEY,
  cliente_id INT,
  codigo INT UNIQUE NOT NULL,
  tipo_codigo VARCHAR(50),
  caso_relacionado VARCHAR(100),
  fecha_asignacion DATE NOT NULL,
  fecha_vencimiento DATE,
  activo BOOLEAN DEFAULT TRUE,
  pago_realizado BOOLEAN DEFAULT FALSE,
  CONSTRAINT codigo_pago_fk_cliente FOREIGN KEY (cliente_id) REFERENCES cliente (cliente_id) ON DELETE CASCADE
);
