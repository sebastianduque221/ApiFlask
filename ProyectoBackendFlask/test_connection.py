import pyodbc

# Cadena de conexión para SQL Server LocalDB
conn_str = (
    r'DRIVER={ODBC Driver 17 for SQL Server};'  # ODBC Driver para SQL Server
    r'SERVER=(localdb)\MSSQLLocalDB;'  # Cambia esto si 'sqllocaldb info' muestra algo diferente
    r'DATABASE=bdfacturas;'  # Base de datos
    r'Trusted_Connection=yes;'
)


try:
    # Intentar abrir la conexión
    conn = pyodbc.connect(conn_str)
    print("Conexión exitosa a la base de datos.")
    
    # Crear un cursor para ejecutar una consulta
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM persona")  # Asumiendo que existe la tabla 'persona'
    
    # Obtener los resultados
    rows = cursor.fetchall()
    
    # Mostrar los resultados
    for row in rows:
        print(row)

    # Cerrar la conexión
    cursor.close()
    conn.close()
    print("Conexión cerrada.")
    
except Exception as ex:
    print(f"Error al conectar o ejecutar consulta: {ex}")
