"""
INTEGRANTE 6 (OPCIONAL: solo si el equipo tiene 6 personas) — service-events: tickets, entradas y compras
(15 pruebas unitarias)

Para ACTIVAR este módulo, renómbralo a:   test_integrante_6_events_servicios.py
(pytest solo ejecuta archivos cuyo nombre empieza con "test_", por eso está desactivado por defecto).

Código bajo prueba (service-events/events/):
  - services.py -> TicketGenerationService.generate_alphanumeric_code(), generate_qr_base64()
  - models.py   -> generate_backup_code(), Event.is_upcoming, TicketType.configured_seats,
                   Purchase.check_expiration(), Purchase.get_user_email()

Las dependencias externas (HTTP a service-profiles, guardado en BD, correo) se reemplazan con
mocks: no hay base de datos ni red. Todas las pruebas siguen el patrón AAA:
  1) PREPARACIÓN (Arrange)  2) LÓGICA (Act)  3) VERIFICACIÓN (Assert)
"""
import base64
import string
import uuid
from datetime import date, timedelta
from unittest.mock import Mock, patch

import requests
from django.utils import timezone

from events.models import Event, Purchase, TicketType, generate_backup_code
from events.services import TicketGenerationService, generate_qr_base64


# ══════════════════════════════════════════════════════════════════════════════
# Códigos y QR de la entrada digital  (pruebas 1 a 5)
# ══════════════════════════════════════════════════════════════════════════════
def cuandoNoSeIndicaLongitud_generateAlphanumericCodeDebeGenerarOchoCaracteresEnMayusculasYDigitos():
    # 1) PREPARACIÓN
    caracteres_permitidos = set(string.ascii_uppercase + string.digits)

    # 2) LÓGICA
    codigo = TicketGenerationService.generate_alphanumeric_code()

    # 3) VERIFICACIÓN
    assert len(codigo) == 8
    assert set(codigo) <= caracteres_permitidos


def cuandoSePideLongitudDoce_generateAlphanumericCodeDebeGenerarDoceCaracteres():
    # 1) PREPARACIÓN
    longitud = 12

    # 2) LÓGICA
    codigo = TicketGenerationService.generate_alphanumeric_code(length=longitud)

    # 3) VERIFICACIÓN
    assert len(codigo) == 12


def cuandoSeGeneraUnQrConTextoValido_generateQrBase64DebeRetornarUnaImagenPng():
    # 1) PREPARACIÓN
    contenido = "VERIFY|TICKET:123|USER:456|CODE:ABCD1234"

    # 2) LÓGICA
    qr_base64 = generate_qr_base64(contenido)
    bytes_imagen = base64.b64decode(qr_base64)

    # 3) VERIFICACIÓN
    assert bytes_imagen.startswith(b"\x89PNG")  # firma de archivo PNG


def cuandoSeGeneraUnCodigoDeRespaldo_generateBackupCodeDebeTenerDiezCaracteresHexadecimalesEnMayusculas():
    # 1) PREPARACIÓN
    hexadecimales_mayuscula = set("0123456789ABCDEF")

    # 2) LÓGICA
    codigo = generate_backup_code()

    # 3) VERIFICACIÓN
    assert len(codigo) == 10
    assert set(codigo) <= hexadecimales_mayuscula


def cuandoSeGeneranDosCodigosDeRespaldo_generateBackupCodeDebeProducirValoresDistintos():
    # 1) PREPARACIÓN
    cantidad = 2

    # 2) LÓGICA
    codigos = {generate_backup_code() for _ in range(cantidad)}

    # 3) VERIFICACIÓN
    assert len(codigos) == 2


# ══════════════════════════════════════════════════════════════════════════════
# Propiedades de Event y TicketType  (pruebas 6 a 9)
# ══════════════════════════════════════════════════════════════════════════════
def cuandoLaFechaDelEventoEsFutura_isUpcomingDebeSerTrue():
    # 1) PREPARACIÓN
    evento = Event(event_date=date.today() + timedelta(days=10))

    # 2) LÓGICA
    es_proximo = evento.is_upcoming

    # 3) VERIFICACIÓN
    assert es_proximo is True


def cuandoLaFechaDelEventoYaPaso_isUpcomingDebeSerFalse():
    # 1) PREPARACIÓN
    evento = Event(event_date=date.today() - timedelta(days=1))

    # 2) LÓGICA
    es_proximo = evento.is_upcoming

    # 3) VERIFICACIÓN
    assert es_proximo is False


def cuandoSeConfiguranFilasYAsientosPorFila_configuredSeatsDebeRetornarSuProducto():
    # 1) PREPARACIÓN
    zona = TicketType(seat_rows=5, seats_per_row=10)

    # 2) LÓGICA
    asientos = zona.configured_seats

    # 3) VERIFICACIÓN
    assert asientos == 50


def cuandoFaltaLaCantidadDeAsientosPorFila_configuredSeatsDebeRetornarNone():
    # 1) PREPARACIÓN
    zona = TicketType(seat_rows=5, seats_per_row=None)

    # 2) LÓGICA
    asientos = zona.configured_seats

    # 3) VERIFICACIÓN
    assert asientos is None


# ══════════════════════════════════════════════════════════════════════════════
# Purchase.check_expiration  (pruebas 10 a 12)
# ══════════════════════════════════════════════════════════════════════════════
def cuandoLaCompraYaEstaActiva_checkExpirationDebeRetornarFalseSinCambiarElEstado():
    # 1) PREPARACIÓN
    compra = Purchase(status="active", created_at=timezone.now() - timedelta(hours=1))

    # 2) LÓGICA
    expiro = compra.check_expiration()

    # 3) VERIFICACIÓN
    assert expiro is False
    assert compra.status == "active"


def cuandoLaCompraPendienteSuperaElTiempoLimite_checkExpirationDebeMarcarlaExpiradaYLiberarAsientos():
    # 1) PREPARACIÓN
    compra = Purchase(status="pending", created_at=timezone.now() - timedelta(hours=1))

    # 2) LÓGICA (guardado en BD, liberación de asientos y correo se reemplazan con mocks)
    with patch.object(Purchase, "save") as guardar, \
         patch.object(Purchase, "release_seats") as liberar_asientos, \
         patch.object(Purchase, "send_expiration_email") as enviar_correo:
        expiro = compra.check_expiration()

    # 3) VERIFICACIÓN
    assert expiro is True
    assert compra.status == "expired"
    guardar.assert_called_once_with(update_fields=["status"])
    liberar_asientos.assert_called_once()
    enviar_correo.assert_called_once()


def cuandoLaCompraPendienteFueCreadaRecientemente_checkExpirationDebeRetornarFalse():
    # 1) PREPARACIÓN
    compra = Purchase(status="pending", created_at=timezone.now())

    # 2) LÓGICA
    expiro = compra.check_expiration()

    # 3) VERIFICACIÓN
    assert expiro is False
    assert compra.status == "pending"


# ══════════════════════════════════════════════════════════════════════════════
# Purchase.get_user_email (consulta HTTP a service-profiles)  (pruebas 13 a 15)
# ══════════════════════════════════════════════════════════════════════════════
def cuandoServicePerfilesResponde200ConEmail_getUserEmailDebeRetornarElEmail():
    # 1) PREPARACIÓN
    id_usuario = uuid.uuid4()
    compra = Purchase(user_id=id_usuario)
    respuesta_falsa = Mock(status_code=200)
    respuesta_falsa.json.return_value = {"email": "cliente@ticketgo.com"}

    # 2) LÓGICA
    with patch("events.models.requests.get", return_value=respuesta_falsa) as peticion:
        email = compra.get_user_email()

    # 3) VERIFICACIÓN
    assert email == "cliente@ticketgo.com"
    peticion.assert_called_once_with(
        f"http://servicio-perfiles.test/api/profiles/{id_usuario}/", timeout=5
    )


def cuandoServicePerfilesResponde404_getUserEmailDebeRetornarNone():
    # 1) PREPARACIÓN
    compra = Purchase(user_id=uuid.uuid4())
    respuesta_falsa = Mock(status_code=404)

    # 2) LÓGICA
    with patch("events.models.requests.get", return_value=respuesta_falsa):
        email = compra.get_user_email()

    # 3) VERIFICACIÓN
    assert email is None


def cuandoFallaLaConexionConServicePerfiles_getUserEmailDebeRetornarNoneSinLanzarExcepcion():
    # 1) PREPARACIÓN
    compra = Purchase(user_id=uuid.uuid4())
    error_de_red = requests.ConnectionError("servicio caído")

    # 2) LÓGICA
    with patch("events.models.requests.get", side_effect=error_de_red):
        email = compra.get_user_email()

    # 3) VERIFICACIÓN
    assert email is None
