# models/Entidad.py
from typing import Any, Dict

class Entidad:
    def __init__(self, propiedades_iniciales: Dict[str, Any] = None):
        # Inicializa un diccionario de propiedades. Si no se pasa uno, crea un diccionario vacío.
        self.propiedades = propiedades_iniciales if propiedades_iniciales is not None else {}

    def __getitem__(self, nombre: str) -> Any:
        # Obtiene el valor asociado a la clave (nombre). Retorna None si no existe.
        return self.propiedades.get(nombre)

    def __setitem__(self, nombre: str, valor: Any) -> None:
        # Asigna un valor a la clave especificada.
        self.propiedades[nombre] = valor

    def obtener_propiedades(self) -> Dict[str, Any]:
        # Devuelve una copia del diccionario de propiedades.
        return dict(self.propiedades)
