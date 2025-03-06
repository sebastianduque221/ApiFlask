import os
import pyodbc
from dotenv import load_dotenv

# Cargar las variables del archivo .env
load_dotenv()

class ControlConexion:
    def __init__(self):
        self._conexion_bd = None  # Variable para almacenar la conexión a la base de datos
        self._proveedor = os.getenv("DATABASE_PROVIDER")  # Proveedor de base de datos
        self._cadena_conexion = os.getenv(f"{self._proveedor.upper()}_CONNECTION_STRING")  # Cadena de conexión

    # Método para abrir la base de datos
    def abrir_bd(self):
        try:
            # Verifica si el proveedor y la cadena de conexión están configurados
            if not self._proveedor or not self._cadena_conexion:
                raise ValueError("Proveedor de base de datos o cadena de conexión no configurados.")

            print(f"Intentando abrir conexión con el proveedor: {self._proveedor}")
            print(f"Cadena de conexión: {self._cadena_conexion}")

            # Abre la conexión según el proveedor configurado
            if self._proveedor in ["LocalDb", "SqlServer"]:
                # Usar pyodbc para conectarse a SQL Server y LocalDb
                self._conexion_bd = pyodbc.connect(self._cadena_conexion)
            else:
                raise ValueError("Proveedor de base de datos no soportado. Solo se soportan LocalDb y SqlServer.")
            
            print("Conexión a la base de datos abierta exitosamente.")
        except Exception as ex:
            print(f"Ocurrió una excepción: {str(ex)}")
            raise RuntimeError("No se pudo abrir la conexión a la base de datos.") from ex

    # Método para cerrar la conexión a la base de datos
    def cerrar_bd(self):
        try:
            # Verifica si la conexión está abierta y luego la cierra
            if self._conexion_bd:
                self._conexion_bd.close()
                print("Conexión a la base de datos cerrada exitosamente.")
        except Exception as ex:
            print(f"Ocurrió una excepción al cerrar la conexión: {str(ex)}")
            raise RuntimeError("No se pudo cerrar la conexión a la base de datos.") from ex

    # Método para ejecutar un comando SQL y devolver el número de filas afectadas
    def ejecutar_comando_sql(self, consulta_sql, parametros=None):
        try:
            # Verifica si la conexión está abierta antes de ejecutar el comando
            if not self._conexion_bd:
                raise RuntimeError("La conexión a la base de datos no está abierta.")

            # Crea un cursor para ejecutar el comando SQL
            cursor = self._conexion_bd.cursor()
            print(f"Ejecutando comando: {consulta_sql}")

            # Ejecuta el comando con los parámetros proporcionados
            if parametros:
                print(f"Parámetros: {parametros}")
                cursor.execute(consulta_sql, parametros)
            else:
                cursor.execute(consulta_sql)

            # Realiza commit para guardar los cambios
            self._conexion_bd.commit()
            filas_afectadas = cursor.rowcount
            print(f"Número de filas afectadas: {filas_afectadas}")
            return filas_afectadas
        except Exception as ex:
            print(f"Ocurrió una excepción: {str(ex)}")
            raise RuntimeError("No se pudo ejecutar el comando SQL.") from ex

    # Método para ejecutar una consulta SQL y devolver los resultados como una lista de diccionarios
    def ejecutar_consulta_sql(self, consulta_sql, parametros=None):
        try:
            # Verifica si la conexión está abierta antes de ejecutar la consulta
            if not self._conexion_bd:
                raise RuntimeError("La conexión a la base de datos no está abierta.")

            # Crea un cursor para ejecutar la consulta
            cursor = self._conexion_bd.cursor()
            print(f"Ejecutando consulta: {consulta_sql}")

            # Ejecuta la consulta con los parámetros proporcionados
            if parametros:
                print(f"Parámetros: {parametros}")
                cursor.execute(consulta_sql, parametros)
            else:
                cursor.execute(consulta_sql)

            # Obtiene todos los resultados de la consulta
            resultado = cursor.fetchall()
            columnas = [column[0] for column in cursor.description]

            # Convierte los resultados en una lista de diccionarios
            filas = [dict(zip(columnas, fila)) for fila in resultado]
            print(f"Número de filas devueltas: {len(filas)}")
            return filas
        except Exception as ex:
            print(f"Ocurrió una excepción: {str(ex)}")
            raise RuntimeError("No se pudo ejecutar la consulta SQL.") from ex

    # Método para crear un parámetro de consulta SQL
    def crear_parametro(self, nombre, valor):
        # En Python, los parámetros se manejan como un simple par clave-valor
        return (nombre, valor)
