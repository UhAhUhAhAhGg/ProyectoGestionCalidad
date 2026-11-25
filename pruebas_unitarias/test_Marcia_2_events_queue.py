import base64
from datetime import date
from types import SimpleNamespace

import pytest

from events.services import TicketGenerationService, generate_qr_base64
from queue_app import active_users
from queue_app.serializers import QueueConfigWriteSerializer


@pytest.fixture(autouse=True)
def aislar_usuarios_activos(monkeypatch):
    monkeypatch.setattr(active_users, "_active_sessions", {})


# Prueba 1: registra actividad y verifica que el usuario quede activo.
def cuandoSeRegistraActividad_debeMarcarUsuarioActivo():
    active_users.register_user_activity("evento-1", "usuario-1")

    assert active_users.is_user_active("evento-1", "usuario-1")


# Prueba 2: actualiza la actividad sin contar dos veces al mismo usuario.
def cuandoSeRegistraActividadDosVeces_debeActualizarSinDuplicar(monkeypatch):
    reloj = [1000]
    monkeypatch.setattr(active_users.time, "time", lambda: reloj[0])

    active_users.register_user_activity("evento-1", "usuario-1")
    reloj[0] = 1010
    active_users.register_user_activity("evento-1", "usuario-1")

    assert active_users.get_active_users_count("evento-1") == 1
    assert active_users._active_sessions["evento-1"]["usuario-1"] == 1010


# Prueba 3: elimina la actividad registrada para un usuario.
def cuandoSeEliminaActividad_debeQuitarAlUsuario():
    active_users.register_user_activity("evento-1", "usuario-1")

    active_users.remove_user_activity("evento-1", "usuario-1")

    assert not active_users.is_user_active("evento-1", "usuario-1")


# Prueba 4: eliminar un usuario inexistente no altera la cola.
def cuandoSeEliminaUsuarioInexistente_debeMantenerLaColaSinCambios():
    active_users.register_user_activity("evento-1", "usuario-1")

    active_users.remove_user_activity("evento-1", "usuario-inexistente")

    assert active_users.get_active_users_count("evento-1") == 1


# Prueba 5: limpiar un evento conserva la actividad de los otros eventos.
def cuandoSeLimpiaUnEvento_debeConservarActividadDeOtrosEventos():
    active_users.register_user_activity("evento-1", "usuario-1")
    active_users.register_user_activity("evento-2", "usuario-2")

    active_users.clear_event_activity("evento-1")

    assert active_users.get_active_users_count("evento-1") == 0
    assert active_users.get_active_users_count("evento-2") == 1


# Prueba 6: excluye del conteo la actividad vencida por el timeout predeterminado.
def cuandoLaActividadSuperaElTiempoPredeterminado_debeExcluirAlUsuario(monkeypatch):
    reloj = [1000]
    monkeypatch.setattr(active_users.time, "time", lambda: reloj[0])

    active_users.register_user_activity("evento-1", "usuario-1")
    reloj[0] = 1121

    assert active_users.get_active_users_count("evento-1") == 0


# Prueba 7: aplica el límite de expiración personalizado.
def cuandoSeUsaUnTimeoutPersonalizado_debeRespetarEseLimite(monkeypatch):
    reloj = [1000]
    monkeypatch.setattr(active_users.time, "time", lambda: reloj[0])

    active_users.register_user_activity("evento-1", "usuario-1")
    reloj[0] = 1059
    assert active_users.is_user_active("evento-1", "usuario-1", timeout_minutes=1)

    reloj[0] = 1061
    assert not active_users.is_user_active("evento-1", "usuario-1", timeout_minutes=1)


# Prueba 8: acepta una configuración de cola con valores positivos.
def cuandoLaConfiguracionDeColaEsValida_debeAceptarAmbosValores():
    serializer = QueueConfigWriteSerializer(
        data={"max_concurrent_users": 25, "payment_timeout_minutes": 10}
    )

    assert serializer.is_valid()
    assert serializer.validated_data == {
        "max_concurrent_users": 25,
        "payment_timeout_minutes": 10,
    }


# Prueba 9: rechaza el umbral de cola igual a cero.
def cuandoElUmbralDeColaEsCero_debeRechazarLaConfiguracion():
    serializer = QueueConfigWriteSerializer(
        data={"max_concurrent_users": 0, "payment_timeout_minutes": 10}
    )

    assert not serializer.is_valid()
    assert "max_concurrent_users" in serializer.errors


# Prueba 10: rechaza un umbral de cola negativo.
def cuandoElUmbralDeColaEsNegativo_debeRechazarLaConfiguracion():
    serializer = QueueConfigWriteSerializer(
        data={"max_concurrent_users": -1, "payment_timeout_minutes": 10}
    )

    assert not serializer.is_valid()
    assert "max_concurrent_users" in serializer.errors


# Prueba 11: rechaza un timeout de pago igual a cero.
def cuandoElTimeoutDePagoEsCero_debeRechazarLaConfiguracion():
    serializer = QueueConfigWriteSerializer(
        data={"max_concurrent_users": 25, "payment_timeout_minutes": 0}
    )

    assert not serializer.is_valid()
    assert "payment_timeout_minutes" in serializer.errors


# Prueba 12: verifica el formato predeterminado del código de emergencia.
def cuandoSeGeneraCodigoDeEmergencia_debeTenerOchoCaracteresAlfanumericos():
    codigo = TicketGenerationService.generate_alphanumeric_code()

    assert len(codigo) == 8
    assert all(caracter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" for caracter in codigo)


# Prueba 13: verifica que el código respete la longitud solicitada.
def cuandoSeSolicitaLongitudPersonalizada_debeGenerarCodigoConEsaLongitud():
    codigo = TicketGenerationService.generate_alphanumeric_code(length=14)

    assert len(codigo) == 14
    assert all(caracter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" for caracter in codigo)


# Prueba 14: decodifica el QR Base64 y comprueba que sea una imagen PNG.
def cuandoSeGeneraUnQrBase64_debeDecodificarComoImagenPng():
    imagen = base64.b64decode(generate_qr_base64("ticket-de-prueba"))

    assert imagen.startswith(b"\x89PNG\r\n\x1a\n")


# Prueba 15: verifica que la entrada digital incluya código, QR y PDF válido.
def cuandoSeGeneraUnaEntradaDigital_debeIncluirQrCodigoYDocumentoPdf():
    evento = SimpleNamespace(
        name="Concierto de prueba",
        event_date=date(2026, 12, 1),
        location="La Paz",
    )
    tipo_entrada = SimpleNamespace(name="General", price="50.00")

    resultado = TicketGenerationService.generate_digital_ticket(
        purchase_id="compra-123",
        event=evento,
        ticket_type=tipo_entrada,
        buyer_id="usuario-456",
    )

    assert set(resultado) == {
        "emergency_code",
        "qr_image_base64",
        "pdf_document_base64",
    }
    assert len(resultado["emergency_code"]) == 8
    assert resultado["qr_image_base64"].startswith("data:image/png;base64,")
    pdf = base64.b64decode(resultado["pdf_document_base64"])
    assert pdf.startswith(b"%PDF-")
