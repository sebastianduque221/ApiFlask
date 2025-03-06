import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from services.ControlConexion import ControlConexion
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import os
from werkzeug.security import generate_password_hash
import bcrypt

# Cargar las variables desde .env
load_dotenv()

# Crear la aplicación Flask
app = Flask(__name__)

# Configurar la conexión a la base de datos y otros ajustes desde config.py
app.config.from_pyfile('config.py')

# Configuración JWT
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')  # Clave secreta desde .env
jwt = JWTManager(app)

# Instancia para la conexión a la base de datos (similar a agregar singleton)
control_conexion = ControlConexion()

# Configurar CORS para permitir solicitudes de cualquier origen (similar a AllowAllOrigins en C#)
CORS(app)

# Activar el modo de desarrollo si estamos en ese entorno
if os.getenv('FLASK_ENV') == 'development':
    app.config['DEBUG'] = True  # Activa la página detallada de excepciones
    app.config['ENV'] = 'development'


@app.route('/')
def home():
    return "¡Bienvenido a la API Flask!"

# Ruta para listar entidades
@app.route('/api/<string:proyecto>/<string:tabla>', methods=['GET'])
#@jwt_required()  # Requiere autenticación JWT para acceder a esta ruta
def listar_entidades(proyecto, tabla):
    """Listar todas las filas de una tabla dada"""
    if not tabla.strip():
        return jsonify({"mensaje": "El nombre de la tabla no puede estar vacío."}), 400

    try:
        control_conexion.abrir_bd()  # Abre la conexión a la base de datos
        comando_sql = f"SELECT * FROM {tabla}"
        resultado = control_conexion.ejecutar_consulta_sql(comando_sql, None)
        control_conexion.cerrar_bd()  # Cierra la conexión a la base de datos

        lista = [dict(fila) for fila in resultado]
        return jsonify(lista), 200
    except Exception as ex:
        return jsonify({"error": str(ex)}), 500


# Ruta para obtener una entidad por una clave específica
@app.route('/api/<string:proyecto>/<string:tabla>/<string:clave>/<string:valor>', methods=['GET'])
#@jwt_required() 
def obtener_entidad_por_clave(proyecto, tabla, clave, valor):
    """Obtener una fila específica de una tabla basada en una clave y su valor"""
    if not tabla.strip() or not clave.strip() or not valor.strip():
        return jsonify({"mensaje": "El nombre de la tabla, clave y valor no pueden estar vacíos."}), 400

    try:
        control_conexion.abrir_bd()
        
        # Consulta para obtener el tipo de dato de la columna
        comando_sql = """
            SELECT data_type FROM information_schema.columns 
            WHERE table_name = ? AND column_name = ?
        """
        tipo_dato_resultado = control_conexion.ejecutar_consulta_sql(comando_sql, (tabla, clave))
        
        if not tipo_dato_resultado or len(tipo_dato_resultado) == 0:
            return jsonify({"mensaje": "No se pudo determinar el tipo de dato."}), 404

        data_type = tipo_dato_resultado[0]['data_type'].lower()
        print(f"Tipo de dato detectado para {clave}: {data_type}")
        
        # Construcción de la consulta SQL según el tipo de dato
        comando_sql = f"SELECT * FROM {tabla} WHERE {clave} = ?"
        converted_value = valor
        
        if data_type in ["int", "bigint", "smallint", "tinyint"]:
            try:
                converted_value = int(valor)
            except ValueError:
                return jsonify({"mensaje": "El valor proporcionado no es válido para el tipo de datos entero."}), 400
        elif data_type in ["decimal", "numeric", "money", "smallmoney"]:
            try:
                converted_value = float(valor)
            except ValueError:
                return jsonify({"mensaje": "El valor proporcionado no es válido para el tipo de datos decimal."}), 400
        elif data_type in ["bit"]:
            if valor.lower() in ["true", "false"]:
                converted_value = valor.lower() == "true"
            else:
                return jsonify({"mensaje": "El valor proporcionado no es válido para el tipo de datos booleano."}), 400
        elif data_type in ["float", "real"]:
            try:
                converted_value = float(valor)
            except ValueError:
                return jsonify({"mensaje": "El valor proporcionado no es válido para el tipo de datos flotante."}), 400
        elif data_type in ["nvarchar", "varchar", "nchar", "char", "text"]:
            # No necesita conversión, solo se usa el valor original
            converted_value = valor
        elif data_type in ["date", "datetime", "datetime2", "smalldatetime"]:
            try:
                converted_value = datetime.strptime(valor, "%Y-%m-%d")
                comando_sql = f"SELECT * FROM {tabla} WHERE CAST({clave} AS DATE) = ?"
            except ValueError:
                return jsonify({"mensaje": "El valor proporcionado no es válido para el tipo de datos fecha."}), 400
        else:
            return jsonify({"mensaje": f"Tipo de dato no soportado: {data_type}"}), 400
        
        print(f"Ejecutando consulta SQL: {comando_sql} con valor: {converted_value}")
        
        # Ejecutar la consulta SQL
        resultado = control_conexion.ejecutar_consulta_sql(comando_sql, (converted_value,))
        control_conexion.cerrar_bd()
        
        if len(resultado) == 0:
            return jsonify({"mensaje": "Entidad no encontrada"}), 404

        return jsonify(resultado), 200

    except Exception as ex:
        print(f"Error: {str(ex)}")
        return jsonify({"error": "No se pudo ejecutar la consulta SQL."}), 500

# Ruta para crear una nueva entidad
@app.route('/api/<string:proyecto>/<string:tabla>', methods=['POST'])
#@jwt_required() 
def crear_entidad(proyecto, tabla):
    """Crear una nueva fila en la tabla especificada"""
    datos = request.get_json()
    if not datos:
        return jsonify({"mensaje": "Los datos de la entidad no pueden estar vacíos."}), 400

    try:
        # Verificar si hay un campo de contraseña y hashearlo si es necesario con bcrypt
        password_keys = ['password', 'contrasena', 'passw']  # Lista de posibles nombres para el campo de contraseña
        for key in datos:
            if any(pk in key.lower() for pk in password_keys):  # Si detecta un campo de contraseña
                plain_password = datos[key]
                if plain_password:  # Si el campo de contraseña no está vacío
                    hashed_password = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt())  # Hashea la contraseña
                    datos[key] = hashed_password.decode('utf-8')  # Guardar el hash como string

        # Construir la consulta SQL
        columnas = ', '.join(datos.keys())
        valores_placeholder = ', '.join(['?'] * len(datos))  # Cambiado a '?' para que sea compatible con pyodbc y SQL Server
        comando_sql = f"INSERT INTO {tabla} ({columnas}) VALUES ({valores_placeholder})"
        
        # Ejecutar la consulta SQL
        valores = tuple(datos.values())
        control_conexion.abrir_bd()
        control_conexion.ejecutar_comando_sql(comando_sql, valores)
        control_conexion.cerrar_bd()

        return jsonify({"mensaje": "Entidad creada exitosamente."}), 201
    except Exception as ex:
        return jsonify({"error": str(ex)}), 500


# Ruta para actualizar una entidad
@app.route('/api/<string:proyecto>/<string:tabla>/<string:clave>/<string:valor>', methods=['PUT'])
#@jwt_required()
def actualizar_entidad(proyecto, tabla, clave, valor):
    """Actualizar una fila en la tabla basada en una clave"""
    entidad_data = request.get_json()  # Obtiene los datos enviados en el cuerpo de la solicitud

    if not entidad_data:
        return jsonify({"mensaje": "Los datos de la entidad no pueden estar vacíos."}), 400

    try:
        # Verificar si hay un campo de contraseña y hashearlo si es necesario con bcrypt
        password_keys = ['password', 'contrasena', 'passw']  # Lista de posibles nombres para el campo de contraseña
        for key in entidad_data:
            if any(pk in key.lower() for pk in password_keys):  # Si detecta un campo de contraseña
                plain_password = entidad_data[key]
                if plain_password:  # Si el campo de contraseña no está vacío
                    hashed_password = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt())  # Hashea la contraseña
                    entidad_data[key] = hashed_password.decode('utf-8')  # Guardar el hash como string

        # Construir la consulta SQL para la actualización
        actualizaciones = ', '.join([f"{k} = ?" for k in entidad_data.keys()])  # Crear las asignaciones para SET
        comando_sql = f"UPDATE {tabla} SET {actualizaciones} WHERE {clave} = ?"

        # Construir los valores para la consulta, incluyendo el valor de la clave
        valores = list(entidad_data.values()) + [valor]

        # Ejecutar la consulta SQL
        control_conexion.abrir_bd()  # Abre la conexión a la base de datos
        control_conexion.ejecutar_comando_sql(comando_sql, valores)  # Ejecuta la actualización
        control_conexion.cerrar_bd()  # Cierra la conexión

        return jsonify({"mensaje": "Entidad actualizada exitosamente."}), 200
    except Exception as ex:
        return jsonify({"error": str(ex)}), 500


# Ruta para eliminar una entidad
@app.route('/api/<string:proyecto>/<string:tabla>/<string:clave>/<string:valor>', methods=['DELETE'])
#@jwt_required()
def eliminar_entidad(proyecto, tabla, clave, valor):
    """Eliminar una fila de la tabla basada en una clave"""
    if not tabla.strip() or not clave.strip():
        return jsonify({"mensaje": "El nombre de la tabla o clave no pueden estar vacíos."}), 400

    try:
        # Usar ? como marcador de parámetros para SQL Server ODBC
        comando_sql = f"DELETE FROM {tabla} WHERE {clave} = ?"
        control_conexion.abrir_bd()
        control_conexion.ejecutar_comando_sql(comando_sql, (valor,))
        control_conexion.cerrar_bd()

        return jsonify({"mensaje": "Entidad eliminada exitosamente."}), 200
    except Exception as ex:
        return jsonify({"error": str(ex)}), 500


@app.route('/api/<string:proyecto>/ejecutar-consulta-parametrizada', methods=['POST'])
def ejecutar_consulta_parametrizada(proyecto):
    """Ejecutar una consulta SQL parametrizada"""
    cuerpo_solicitud = request.get_json()

    try:
        # Verificar si el cuerpo de la solicitud contiene la consulta SQL
        if 'consulta' not in cuerpo_solicitud or not cuerpo_solicitud['consulta']:
            return jsonify({"mensaje": "Debe proporcionar una consulta SQL válida en el cuerpo de la solicitud."}), 400

        consulta_sql = cuerpo_solicitud['consulta']

        # Verificar si el cuerpo de la solicitud contiene los parámetros
        parametros = []
        if 'parametros' in cuerpo_solicitud and isinstance(cuerpo_solicitud['parametros'], dict):
            for clave, valor in cuerpo_solicitud['parametros'].items():
                parametros.append(valor)  # Agrega los valores directamente como tupla

        # Abrir la conexión a la base de datos
        control_conexion.abrir_bd()

        # Ejecutar la consulta SQL con los parámetros
        resultado = control_conexion.ejecutar_consulta_sql(consulta_sql, parametros)

        # Cerrar la conexión a la base de datos
        control_conexion.cerrar_bd()

        # Verificar si hay resultados
        if len(resultado) == 0:
            return jsonify({"mensaje": "No se encontraron resultados para la consulta proporcionada."}), 404

        # Procesar resultados a formato JSON
        lista = [dict(fila) for fila in resultado]

        return jsonify(lista), 200

    except Exception as ex:
        # Manejo de excepciones
        control_conexion.cerrar_bd()
        print(f"Error: {str(ex)}")
        return jsonify({"error": "Se presentó un error:", "detalle": str(ex)}), 500


# Ruta de ejemplo para autenticación (login) - genera un token JWT
@app.route('/api/login', methods=['POST'])
def login():
    """Autenticación de usuario y generación de un token JWT"""
    if not request.is_json:
        return jsonify({"mensaje": "Se requiere un cuerpo en formato JSON"}), 400

    nombre_usuario = request.json.get("username", None)
    contrasena = request.json.get("password", None)

    # Validación de ejemplo (en un caso real, validarías contra una base de datos)
    if nombre_usuario != "admin" or contrasena != "1234":
        return jsonify({"mensaje": "Usuario o contraseña incorrectos"}), 401

    token_acceso = create_access_token(identity=nombre_usuario)
    return jsonify(access_token=token_acceso), 200


# Iniciar la aplicación
if __name__ == '__main__':
    app.run(debug=True, port=5184)


"""
Modos de uso:

GET
http://localhost:5184/api/proyecto/usuario
http://localhost:5184/api/proyecto/usuario/email/admin@empresa.com

POST
http://localhost:5184/api/proyecto/usuario
{
    "email": "nuevo.nuevo@empresa.com",
    "contrasena": "123"
}

PUT
http://localhost:5184/api/proyecto/usuario/email/nuevo.nuevo@empresa.com
{
    "contrasena": "456"
}

DELETE
http://localhost:5184/api/proyecto/usuario/email/nuevo.nuevo@empresa.com
"""
"""
Códigos de estado HTTP:

2xx (Éxito):
- 200 OK: La solicitud ha tenido éxito.
- 201 Creado: La solicitud ha sido completada y ha resultado en la creación de un nuevo recurso.
- 202 Aceptado: La solicitud ha sido aceptada para procesamiento, pero el procesamiento no ha sido completado.
- 203 Información no autoritativa: La respuesta se ha obtenido de una copia en caché en lugar de directamente del servidor original.
- 204 Sin contenido: La solicitud ha tenido éxito pero no hay contenido que devolver.
- 205 Restablecer contenido: La solicitud ha tenido éxito, pero el cliente debe restablecer la vista que ha solicitado.
- 206 Contenido parcial: El servidor está enviando una respuesta parcial del recurso debido a una solicitud Range.

3xx (Redirección):
- 300 Múltiples opciones: El servidor puede responder con una de varias opciones.
- 301 Movido permanentemente: El recurso solicitado ha sido movido de manera permanente a una nueva URL.
- 302 Encontrado: El recurso solicitado reside temporalmente en una URL diferente.
- 303 Ver otros: El servidor dirige al cliente a una URL diferente para obtener la respuesta solicitada (usualmente en una operación POST).
- 304 No modificado: El contenido no ha cambiado desde la última solicitud (usualmente usado con la caché).
- 305 Usar proxy: El recurso solicitado debe ser accedido a través de un proxy.
- 307 Redirección temporal: Similar al 302, pero el cliente debe utilizar el mismo método de solicitud original (GET o POST).
- 308 Redirección permanente: Similar al 301, pero el método de solicitud original debe ser utilizado en la nueva URL.

4xx (Errores del cliente):
- 400 Solicitud incorrecta: La solicitud contiene sintaxis errónea o no puede ser procesada.
- 401 No autorizado: El cliente debe autenticarse para obtener la respuesta solicitada.
- 402 Pago requerido: Este código es reservado para uso futuro, generalmente relacionado con pagos.
- 403 Prohibido: El cliente no tiene permisos para acceder al recurso, incluso si está autenticado.
- 404 No encontrado: El servidor no pudo encontrar el recurso solicitado.
- 405 Método no permitido: El método HTTP utilizado no está permitido para el recurso solicitado.
- 406 No aceptable: El servidor no puede generar una respuesta que coincida con las características aceptadas por el cliente.
- 407 Autenticación de proxy requerida: Similar a 401, pero la autenticación debe hacerse a través de un proxy.
- 408 Tiempo de espera agotado: El cliente no envió una solicitud dentro del tiempo permitido por el servidor.
- 409 Conflicto: La solicitud no pudo ser completada debido a un conflicto en el estado actual del recurso.
- 410 Gone: El recurso solicitado ya no está disponible y no será vuelto a crear.
- 411 Longitud requerida: El servidor requiere que la solicitud especifique una longitud en los encabezados.
- 412 Precondición fallida: Una condición en los encabezados de la solicitud falló.
- 413 Carga útil demasiado grande: El cuerpo de la solicitud es demasiado grande para ser procesado.
- 414 URI demasiado largo: La URI solicitada es demasiado larga para que el servidor la procese.
- 415 Tipo de medio no soportado: El formato de los datos en la solicitud no es compatible con el servidor.
- 416 Rango no satisfactorio: La solicitud incluye un rango que no puede ser satisfecho.
- 417 Fallo en la expectativa: La expectativa indicada en los encabezados de la solicitud no puede ser cumplida.
- 418 Soy una tetera (RFC 2324): Este código es un Easter Egg HTTP. El servidor rechaza la solicitud porque "soy una tetera."
- 421 Mala asignación: El servidor no puede cumplir con la solicitud.
- 426 Se requiere actualización: El cliente debe actualizar el protocolo de solicitud.
- 428 Precondición requerida: El servidor requiere que se cumpla una precondición antes de procesar la solicitud.
- 429 Demasiadas solicitudes: El cliente ha enviado demasiadas solicitudes en un corto periodo de tiempo.
- 431 Campos de encabezado muy grandes: Los campos de encabezado de la solicitud son demasiado grandes.
- 451 No disponible por razones legales: El contenido ha sido bloqueado por razones legales (ej. leyes de copyright).

5xx (Errores del servidor):
- 500 Error interno del servidor: El servidor encontró una situación inesperada que le impidió completar la solicitud.
- 501 No implementado: El servidor no tiene la capacidad de completar la solicitud.
- 502 Puerta de enlace incorrecta: El servidor, al actuar como puerta de enlace o proxy, recibió una respuesta no válida del servidor upstream.
- 503 Servicio no disponible: El servidor no está disponible temporalmente, generalmente debido a mantenimiento o sobrecarga.
- 504 Tiempo de espera de la puerta de enlace: El servidor, al actuar como puerta de enlace o proxy, no recibió una respuesta a tiempo de otro servidor.
- 505 Versión HTTP no soportada: El servidor no soporta la versión HTTP utilizada en la solicitud.
- 506 Variante también negocia: El servidor encontró una referencia circular al negociar el contenido.
- 507 Almacenamiento insuficiente: El servidor no puede almacenar la representación necesaria para completar la solicitud.
- 508 Bucle detectado: El servidor detectó un bucle infinito al procesar la solicitud.
- 510 No extendido: Se requiere la extensión adicional de las políticas de acceso.
- 511 Se requiere autenticación de red: El cliente debe autenticar la red para poder acceder al recurso.
"""

