DELIMITER ;

USE bot_maqui_react;

INSERT INTO cliente (documento_identidad, tipo_documento, nombre, apellido, celular, email)
VALUES (70361965, 'DNI', 'Alicia', 'Cántaro', 953983765, 'patricia@sayainvestments.co');

INSERT INTO cliente (documento_identidad, tipo_documento, nombre, apellido, celular, email)
VALUES (70361967, 'DNI', 'Daniel', 'Castillo', 941729891, 'daniel.castillo@sayainvestments.co');

-- campanha out: se envia el template asociado (todavia falta crear un template en twilio)
INSERT INTO campanha (nombre_campanha, descripcion)
VALUES ('Campaña de prueba out','Esta es una campaña de prueba');

-- campanha in: aqui asociamos a todos los clientes que vienen y no existen en la out (probablementé no se use)
INSERT INTO campanha (nombre_campanha, descripcion, mensaje_cliente)
VALUES ('Campaña de prueba in','Esta es una campaña de prueba','Hola prueba in');

INSERT INTO cliente_campanha (cliente_id, campanha_id)
VALUES (1,1);

INSERT INTO cliente_campanha (cliente_id, campanha_id)
VALUES (2,1);

INSERT INTO rol (nombre_rol, descripcion)
VALUES ('administrador','Gestión de todas las vistas.');

INSERT INTO rol (nombre_rol, descripcion)
VALUES ('asesor','Gestión de clientes y fechas de pago.');

INSERT INTO usuario (username, password, rol_id)
VALUES ('patricia@sayainvestments.co','1234',1);

INSERT INTO persona (persona_id,nombre, primer_apellido, segundo_apellido,celular)
VALUES (1,'Patricia','Cántaro','Márquez','953983765');

