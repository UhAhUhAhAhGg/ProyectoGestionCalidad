
---

# 🧪 Entregable: Pruebas Unitarias con TDD

Pruebas unitarias del backend de **TicketGo** (microservicios Django) escritas con el patrón **AAA**
(Arrange – Act – Assert). Viven en la carpeta [`pruebas_unitarias/`](pruebas_unitarias/).

## 1. Lenguaje(s) de programación del software

| Capa | Lenguaje / tecnología | Dónde |
|---|---|---|
| **Backend (capa que se prueba)** | **Python 3** (≥ 3.10) con **Django 4.2** y **Django REST Framework** | `service-auth/`, `service-events/`, `service-queue/`, `service-profiles/` |
| Frontend (no se prueba en este entregable) | JavaScript / React (Next.js 16) | `frontend/` |

Las pruebas unitarias se implementan sobre la **capa de backend en Python**, donde se concentra la lógica
de negocio (validaciones, permisos, reglas de expiración, control de la cola virtual).

## 2 y 3. Clases/archivos y métodos/funciones con pruebas unitarias, y su objetivo

### Integrante 1 — `service-auth`: validaciones de datos de usuario
| Archivo | Clase / método | Objetivo |
|---|---|---|
| `service-auth/users/serializers.py` | `UserProfileSerializer.validate_phone()` | Valida el teléfono: quita espacios, acepta solo dígitos o `+` inicial y exige mínimo 8 dígitos. |
| `service-auth/users/serializers.py` | `AdminCreateUserSerializer.validate()` | Valida la contraseña (≥ 8 caracteres, 1 mayúscula, 1 número) y exige empresa, NIT y cuenta bancaria si el rol es Promotor. |
| `service-auth/users/models.py` | `UserProfile.full_name` | Devuelve el nombre completo concatenando nombre y apellido. |
| `service-auth/users/models.py` | `UserManager.create_user()` | Crea usuarios y rechaza emails vacíos. |

### Integrante 3 — `service-queue`: control de usuarios activos de la cola virtual
| Archivo | Clase / método | Objetivo |
|---|---|---|
| `service-queue/queue_app/active_users.py` | `register_user_activity()` | Registra o actualiza la actividad de un usuario en la cola de un evento (sin duplicarlo y sin mezclar eventos). |
| `service-queue/queue_app/active_users.py` | `remove_user_activity()` | Quita a un usuario de la cola (p. ej. al completar la compra); no falla si el usuario no existe. |
| `service-queue/queue_app/active_users.py` | `get_active_users_count()` | Devuelve la cantidad de usuarios activos de un evento, descartando antes a los inactivos por más de 2 minutos. |
| `service-queue/queue_app/active_users.py` | `is_user_active()` | Indica si un usuario está activo en un evento; retorna `False` si el evento no existe o si el usuario expiró. |
| `service-queue/queue_app/active_users.py` | `clear_event_activity()` | Vacía la cola de un evento (p. ej. cuando el promotor lo reconfigura) sin afectar a otros eventos. |
| `service-queue/queue_app/models.py` | `SeatReservation.is_expired` | Indica si una reserva temporal de asiento expiró: solo si sigue `active` y ya pasó su `expires_at`. |


> *(Si el equipo es de 5 integrantes, agregar la tabla del Integrante 6: `service-events/events/services.py` y
> `models.py` — generación de códigos/QR, `Event.is_upcoming`, `TicketType.configured_seats`,
> `Purchase.check_expiration()` y `Purchase.get_user_email()`.)*

## 4. Framework de pruebas unitarias

**[pytest](https://docs.pytest.org/)** (familia *xUnit*) junto con **pytest-django**.

| Herramienta | Para qué se usa |
|---|---|
| `pytest` | Descubre y ejecuta las pruebas; reporta resultados y fallos con detalle. Usa `assert` simple y `pytest.raises` para verificar excepciones. |
| `pytest-django` | Integra pytest con Django (carga los settings y los modelos de cada microservicio). |
| `unittest.mock` (`Mock`, `patch`) y `monkeypatch` | Reemplazan dependencias externas (HTTP a otros servicios, guardado en BD, correo, reloj) para que cada prueba sea **aislada, rápida y determinista**. |
| `pytest.ini` + `pruebas_unitarias/settings_pruebas.py` | Configuración exclusiva de pruebas: SQLite en memoria, **sin Docker ni PostgreSQL**. |

Dependencias: [`pruebas_unitarias/requirements-test.txt`](pruebas_unitarias/requirements-test.txt).

### Estructura de cada prueba (patrón AAA) y nombres
Cada prueba tiene las 3 partes exigidas y su verificación explícita:

```python
def cuandoTelefonoTieneEspacios_debeQuitarlosYRetornarNumeroLimpio():
    # 1) PREPARACIÓN (Arrange): objetos y datos de entrada
    serializador = UserProfileSerializer()
    telefono = "712 345 67"

    # 2) LÓGICA (Act): se ejecuta el método bajo prueba
    resultado = serializador.validate_phone(telefono)

    # 3) VERIFICACIÓN (Assert): resultado esperado
    assert resultado == "71234567"
```

Convención de nombres: `cuando<Condición>_<método>Debe<ResultadoEsperado>` (nunca `test1`, `prueba`, etc.).

### TDD (Test-Driven Development)
Ciclo **Red → Green → Refactor**: 1) escribir una prueba que falle (*Red*), 2) escribir el mínimo código para que
pase (*Green*), 3) mejorar el código manteniendo las pruebas en verde (*Refactor*). Las pruebas de este
repositorio fijan las reglas de negocio ya implementadas y protegen cada regla frente a cambios futuros.

## ▶️ Cómo ejecutar las pruebas unitarias

```bash
# Desde la raíz del repositorio
python -m venv venv

# Activar el entorno:
#   Windows (PowerShell):  venv\Scripts\Activate.ps1
#   Windows (CMD):         venv\Scripts\activate.bat
#   Linux / macOS:         source venv/bin/activate

pip install -r pruebas_unitarias/requirements-test.txt
pytest
```

Resultado esperado: **`75 passed`** (todas en verde en teoría 75). No requiere Docker, PostgreSQL ni variables de entorno.

## 5. Distribución 

| Integrante | Archivo | Pruebas |
|---|---|:---:|
| **[Ariana Kremsberger]** | `pruebas_unitarias/test_integrante_1_auth_serializers.py` | 15 |
| **[Luciana]** | `pruebas_unitarias/test_Luciana_3_queue_active_users.py` | 15 |

