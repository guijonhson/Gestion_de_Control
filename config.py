import os
from dotenv import load_dotenv

# Cargar .env ANTES de leer cualquier variable
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    # SECRET_KEY: obligatoria en producción, con fallback seguro en desarrollo
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # SQLite por defecto, pero configurable vía DATABASE_URL
    db_path = os.environ.get('DATABASE_URL')
    if db_path:
        SQLALCHEMY_DATABASE_URI = db_path
    else:
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(BASE_DIR, "database", "agrodev.db")}'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes')
    
    # Configuración CSRF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # Tokens no expiran mientras la sesión esté activa
    
    # Sesiones
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24 * 7  # 7 días


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True  # Solo cookies por HTTPS
    
    def __init__(self):
        if not self.SECRET_KEY:
            raise RuntimeError(
                "SECRET_KEY es obligatoria en producción. "
                "Defínela en el archivo .env o en las variables de entorno."
            )


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    
    # En desarrollo, si no hay SECRET_KEY en .env, usar una fija conocida
    # (así las sesiones sobreviven reinicios durante el desarrollo)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-cambiar-en-produccion'


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False  # Deshabilitar CSRF en tests para simplificar


def get_config():
    env = os.environ.get('FLASK_ENV', 'development')
    if env == 'production':
        return ProductionConfig
    elif env == 'testing':
        return TestingConfig
    return DevelopmentConfig