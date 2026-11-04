"""
settings_pruebas.py
-------------------
Configuración mínima de Django SOLO para ejecutar las pruebas unitarias.

¿Por qué existe?
  Los settings reales de cada microservicio usan PostgreSQL (Docker). Una prueba
  unitaria no debe depender de una base de datos real ni de contenedores, así que
  aquí se usa SQLite en memoria y solo las apps que se prueban.

  Las pruebas de este paquete NO tocan la base de datos: instancian objetos sin
  guardarlos, usan objetos falsos (SimpleNamespace / Mock) y parchean dependencias
  externas (HTTP, correo, reloj).
"""

SECRET_KEY = "clave-solo-para-pruebas-unitarias"
DEBUG = False
USE_TZ = True
TIME_ZONE = "UTC"

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    "rest_framework_simplejwt",
    # Apps de los microservicios que se prueban
    "users",       # service-auth
    "events",      # service-events
    "queue_app",   # service-queue
]

# Mismo modelo de usuario personalizado que usa service-auth
AUTH_USER_MODEL = "users.User"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]  # rápido en pruebas

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
DEFAULT_FROM_EMAIL = "pruebas@ticketgo.test"
PROFILE_SERVICE_URL = "http://servicio-perfiles.test"

SIMPLE_JWT = {
    "SIGNING_KEY": SECRET_KEY,
    "ALGORITHM": "HS256",
}
