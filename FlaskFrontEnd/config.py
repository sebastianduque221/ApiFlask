import os
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "tu_secreto_aqui")  # Clave de sesión
    DEBUG = os.getenv("FLASK_DEBUG", "False") == "True"
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5184/")

class DevelopmentConfig(Config):
    ENV = "development"
    DEBUG = True

class ProductionConfig(Config):
    ENV = "production"
    DEBUG = False

config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}
