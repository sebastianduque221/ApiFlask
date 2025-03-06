import requests

class ApiService:
    """Servicio para manejar las operaciones CRUD con una API externa.
    Proporciona métodos para obtener, añadir, editar y eliminar entidades.
    """

    def __init__(self, base_url):
        """Inicializa el servicio con la URL base de la API."""
        self.base_url = base_url

    def get_data(self, endpoint):
        """Obtiene datos de la API de forma síncrona.

        Args:
            endpoint (str): URL del endpoint de la API.

        Returns:
            list: Una lista de diccionarios representando los datos obtenidos.
        """
        try:
            response = requests.get(f"{self.base_url}{endpoint}")
            response.raise_for_status()  # Asegura que la respuesta sea exitosa (código 2xx)
            return response.json()  # Devuelve el contenido JSON como lista de diccionarios
        except requests.RequestException as e:
            print(f"Error al obtener datos: {e}")
            raise

    def add_entity(self, endpoint, entity):
        """Añade una nueva entidad a través de la API.

        Args:
            endpoint (str): URL del endpoint de la API.
            entity (dict): Diccionario que representa la entidad a añadir.

        Returns:
            bool: True si la operación fue exitosa, False en caso contrario.
        """
        try:
            response = requests.post(f"{self.base_url}{endpoint}", json=entity)
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"Error al añadir entidad: {e}")
            return False

    def edit_entity(self, endpoint, entity_id, entity):
        """Edita una entidad existente a través de la API.

        Args:
            endpoint (str): URL base del endpoint de la API.
            entity_id (str): Identificador de la entidad a editar.
            entity (dict): Diccionario que representa la entidad actualizada.

        Returns:
            bool: True si la operación fue exitosa, False en caso contrario.
        """
        try:
            response = requests.put(f"{self.base_url}{endpoint}/{entity_id}", json=entity)
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"Error al editar entidad: {e}")
            return False

    def delete_entity(self, endpoint, entity_id):
        """Elimina una entidad a través de la API.

        Args:
            endpoint (str): URL base del endpoint de la API.
            entity_id (str): Identificador de la entidad a eliminar.

        Returns:
            bool: True si la operación fue exitosa, False en caso contrario.
        """
        try:
            response = requests.delete(f"{self.base_url}{endpoint}/{entity_id}")
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"Error al eliminar entidad: {e}")
            return False
