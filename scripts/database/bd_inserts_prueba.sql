DELIMITER ;

USE bot_maqui_react;

INSERT INTO cliente (documento_identidad, tipo_documento, nombre, apellido, celular, email)
VALUES (70361965, 'DNI', 'Alicia', 'Cántaro', '+51953983765', 'patricia@sayainvestments.co');

INSERT INTO cliente (documento_identidad, tipo_documento, nombre, apellido, celular, email)
VALUES (70361967, 'DNI', 'Daniel', 'Castillo', '+51941729891', 'daniel.castillo@sayainvestments.co');

INSERT INTO cliente (documento_identidad, tipo_documento, nombre, apellido, celular, email)
VALUES (70361968, 'DNI', 'Marco', 'Roca', '+51989073578', 'marco@sayainvestments.co');

INSERT INTO cliente (documento_identidad, tipo_documento, nombre, apellido, celular, email)
VALUES (70361969, 'DNI', 'Marcelo', 'Almeyda', '+51977298974', 'marcelo@digitallintelligence.com');

INSERT INTO cliente (documento_identidad, tipo_documento, nombre, apellido, celular, email)
VALUES (70361970, 'DNI', 'John', 'Castillo', '+51945827800', 'john@sayainvestments.co');

-- campanha out: se envia el template asociado (todavia falta crear un template en twilio)
INSERT INTO campanha (nombre_campanha, descripcion)
VALUES ('Campaña de prueba out','Esta es una campaña de prueba');

-- campanha in: aqui asociamos a todos los clientes que vienen y no existen en la out (probablementé no se use)
-- INSERT INTO campanha (nombre_campanha, descripcion, mensaje_cliente)
-- VALUES ('Campaña de prueba in','Esta es una campaña de prueba','Hola prueba in');

INSERT INTO cliente_campanha (cliente_id, campanha_id) VALUES (1,1);

INSERT INTO rol (nombre_rol, descripcion)
VALUES ('administrador','Gestión de todas las vistas.');

INSERT INTO rol (nombre_rol, descripcion)
VALUES ('asesor','Gestión de clientes y fechas de pago.');

INSERT INTO usuario (username, password, rol_id)
VALUES ('patricia@sayainvestments.co','1234',1);

INSERT INTO persona (persona_id,nombre, primer_apellido, segundo_apellido,celular)
VALUES (1,'Patricia','Cántaro','Márquez','+51953983765');

INSERT INTO template (nombre_template,mensaje,created_at,template_content_sid,parametro)
VALUES ('envio1','¡Hola, {NOMBRE_CLIENTE}! 👋
Hemos notado que tienes pagos pendientes en tus contratos de Maqui+ y nos gustaría saber cómo podemos ayudarte a reactivarlos. 
¡Esperamos tu respuesta! 😊',CURRENT_TIMESTAMP,'HX23569fa3042566dbd3ba6ceaa1e8e4a1',1);

INSERT INTO template (nombre_template,mensaje,created_at,template_content_sid,parametro)
VALUES ('pruebita','¡Hola! Tienes contratos pendientes y nos gustaría saber por qué no reactivas con nosotros.',CURRENT_TIMESTAMP,'HX57ffed57805b930892ade47f1147bfbe',0);