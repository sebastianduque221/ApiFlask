import os
from dotenv import load_dotenv

# Cargar las variables del archivo .env
load_dotenv()

# Configuración de la aplicación
class Config:
    # Configuraciones JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    JWT_ISSUER = os.getenv('JWT_ISSUER')
    JWT_AUDIENCE = os.getenv('JWT_AUDIENCE')
    
    # Configuración de la cadena de conexión
    DATABASE_PROVIDER = os.getenv('DATABASE_PROVIDER')
    
    # Determinar la cadena de conexión según el proveedor de base de datos
    CONNECTION_STRINGS = {
        'SqlServer': os.getenv('SQLSERVER_CONNECTION_STRING'),
        'LocalDb': os.getenv('LOCALDB_CONNECTION_STRING'),
    }
    SQLALCHEMY_DATABASE_URI = CONNECTION_STRINGS.get(DATABASE_PROVIDER, 'sqlite:///test.db')

    # Configuración adicional de SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False

# Opcional: configuración de desarrollo específica
class DevelopmentConfig(Config):
    DEBUG = True
    ENV = 'development'

# Opcional: configuración de producción específica
class ProductionConfig(Config):
    DEBUG = False
    ENV = 'production'
