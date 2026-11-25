# base64 permite inspeccionar los bytes reales del QR y del PDF devueltos por los servicios.
import base64
# date y SimpleNamespace construyen datos de prueba sin crear modelos ni usar la base de datos.
from datetime import date
from types import SimpleNamespace

import pytest

# Servicio bajo prueba: genera códigos de emergencia, QR y entradas digitales.
from events.services import TicketGenerationService, generate_qr_base64
# Módulos bajo prueba: seguimiento de usuarios y validación de configuración de la cola.
from queue_app import active_users
from queue_app.serializers import QueueConfigWriteSerializer


@pytest.fixture(autouse=True)
def aislar_usuarios_activos(monkeypatch):
    # active_users conserva sesiones en un diccionario global; se sustituye por uno vacío
    # para que una prueba no herede usuarios de otra. pytest restaura el original al finalizar.
    monkeypatch.setattr(active_users, "_active_sessions", {})


# service-queue/queue_app/active_users.py: registro, eliminacion y expiracion.
# Prueba 1: registra actividad y verifica que el usuario quede activo.
def cuandoSeRegistraActividad_debeMarcarUsuarioActivo():
    # Preparación/acción: registra al usuario en la actividad del evento.
    active_users.register_user_activity("evento-1", "usuario-1")

    # Verificación: is_user_active debe encontrarlo para el mismo evento y usuario.
    assert active_users.is_user_active("evento-1", "usuario-1")


# Prueba 2: actualiza la actividad sin contar dos veces al mismo usuario.
def cuandoSeRegistraActividadDosVeces_debeActualizarSinDuplicar(monkeypatch):
    # time.time se reemplaza por un reloj controlable para que la prueba sea determinista.
    reloj = [1000]
    monkeypatch.setattr(active_users.time, "time", lambda: reloj[0])

    # Primera marca: 1000. Segunda marca: 1010, simulando actividad 10 segundos después.
    active_users.register_user_activity("evento-1", "usuario-1")
    reloj[0] = 1010
    active_users.register_user_activity("evento-1", "usuario-1")

    # El usuario no debe duplicarse y su timestamp debe reflejar el segundo registro.
    assert active_users.get_active_users_count("evento-1") == 1
    assert active_users._active_sessions["evento-1"]["usuario-1"] == 1010


# Prueba 3: elimina la actividad registrada para un usuario.
def cuandoSeEliminaActividad_debeQuitarAlUsuario():
    # Se registra primero para comprobar la eliminación sobre una sesión existente.
    active_users.register_user_activity("evento-1", "usuario-1")

    # remove_user_activity representa que el usuario abandona el evento.
    active_users.remove_user_activity("evento-1", "usuario-1")

    # Ya no debe aparecer en la verificación de actividad.
    assert not active_users.is_user_active("evento-1", "usuario-1")


# Prueba 4: eliminar un usuario inexistente no altera la cola.
def cuandoSeEliminaUsuarioInexistente_debeMantenerLaColaSinCambios():
    # Se conserva un usuario válido para comprobar que la operación no lo afecte.
    active_users.register_user_activity("evento-1", "usuario-1")

    # Se intenta eliminar otro usuario, que nunca fue registrado.
    active_users.remove_user_activity("evento-1", "usuario-inexistente")

    # El usuario que si estaba registrado debe permanecer en la cola.
    assert active_users.get_active_users_count("evento-1") == 1


# Prueba 5: limpiar un evento conserva la actividad de los otros eventos.
def cuandoSeLimpiaUnEvento_debeConservarActividadDeOtrosEventos():
    # Se preparan dos sesiones asociadas a eventos diferentes.
    active_users.register_user_activity("evento-1", "usuario-1")
    active_users.register_user_activity("evento-2", "usuario-2")

    # clear_event_activity debe vaciar evento-1 sin borrar evento-2.
    active_users.clear_event_activity("evento-1")

    # La limpieza no debe afectar a los usuarios del segundo evento.
    assert active_users.get_active_users_count("evento-1") == 0
    assert active_users.get_active_users_count("evento-2") == 1


# Prueba 6: excluye del conteo la actividad vencida por el timeout predeterminado.
def cuandoLaActividadSuperaElTiempoPredeterminado_debeExcluirAlUsuario(monkeypatch):
    # El timeout predeterminado es 2 minutos; se simulan 121 segundos de inactividad.
    reloj = [1000]
    monkeypatch.setattr(active_users.time, "time", lambda: reloj[0])

    active_users.register_user_activity("evento-1", "usuario-1")
    reloj[0] = 1121

    # get_active_users_count limpia sesiones vencidas antes de devolver el total.
    assert active_users.get_active_users_count("evento-1") == 0


# Prueba 7: aplica el límite de expiración personalizado.
def cuandoSeUsaUnTimeoutPersonalizado_debeRespetarEseLimite(monkeypatch):
    # Se simula un timeout personalizado de 1 minuto usando un reloj controlado.
    reloj = [1000]
    monkeypatch.setattr(active_users.time, "time", lambda: reloj[0])

    active_users.register_user_activity("evento-1", "usuario-1")
    reloj[0] = 1059
    # A los 59 segundos aún no se superó el límite de 60 segundos.
    assert active_users.is_user_active("evento-1", "usuario-1", timeout_minutes=1)

    reloj[0] = 1061
    # A los 61 segundos sí se superó el límite y debe considerarse expirado.
    assert not active_users.is_user_active("evento-1", "usuario-1", timeout_minutes=1)


# service-queue/queue_app/serializers.py: validacion de la configuracion de cola.
# Prueba 8: acepta una configuración de cola con valores positivos.
def cuandoLaConfiguracionDeColaEsValida_debeAceptarAmbosValores():
    # Se valida la entrada como si viniera de la API; is_valid no guarda en la base de datos.
    serializer = QueueConfigWriteSerializer(
        data={"max_concurrent_users": 25, "payment_timeout_minutes": 10}
    )

    # Ambos campos deben validarse y conservar sus valores en validated_data.
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

    # El serializer debe rechazar cero porque max_concurrent_users debe ser mayor que 0.
    # También se comprueba que el error quede asociado al campo correcto.
    assert not serializer.is_valid()
    assert "max_concurrent_users" in serializer.errors


# Prueba 10: rechaza un umbral de cola negativo.
def cuandoElUmbralDeColaEsNegativo_debeRechazarLaConfiguracion():
    serializer = QueueConfigWriteSerializer(
        data={"max_concurrent_users": -1, "payment_timeout_minutes": 10}
    )

    # Un umbral negativo es inválido y debe producir un error en max_concurrent_users.
    assert not serializer.is_valid()
    assert "max_concurrent_users" in serializer.errors


# Prueba 11: rechaza un timeout de pago igual a cero.
def cuandoElTimeoutDePagoEsCero_debeRechazarLaConfiguracion():
    serializer = QueueConfigWriteSerializer(
        data={"max_concurrent_users": 25, "payment_timeout_minutes": 0}
    )

    # Cero no es un timeout válido; el serializer debe señalar payment_timeout_minutes.
    assert not serializer.is_valid()
    assert "payment_timeout_minutes" in serializer.errors


# service-events/events/services.py: generacion de codigo, QR y entrada digital.
# Prueba 12: verifica el formato predeterminado del código de emergencia.
def cuandoSeGeneraCodigoDeEmergencia_debeTenerOchoCaracteresAlfanumericos():
    # Sin argumento, el servicio debe usar su longitud predeterminada de 8 caracteres.
    codigo = TicketGenerationService.generate_alphanumeric_code()

    # Cada carácter debe pertenecer al alfabeto permitido: A-Z o 0-9.
    assert len(codigo) == 8
    assert all(caracter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" for caracter in codigo)


# Prueba 13: verifica que el código respete la longitud solicitada.
def cuandoSeSolicitaLongitudPersonalizada_debeGenerarCodigoConEsaLongitud():
    # Se solicita una longitud distinta al valor predeterminado.
    codigo = TicketGenerationService.generate_alphanumeric_code(length=14)

    # El servicio debe respetar los 14 caracteres y mantener el alfabeto A-Z/0-9.
    assert len(codigo) == 14
    assert all(caracter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" for caracter in codigo)


# Prueba 14: decodifica el QR Base64 y comprueba que sea una imagen PNG.
def cuandoSeGeneraUnQrBase64_debeDecodificarComoImagenPng():
    # El servicio devuelve texto Base64; se convierte a bytes para inspeccionar la imagen.
    imagen = base64.b64decode(generate_qr_base64("ticket-de-prueba"))

    # La firma PNG (8 bytes iniciales) confirma que el contenido es una imagen PNG.
    assert imagen.startswith(b"\x89PNG\r\n\x1a\n")


# Prueba 15: verifica que la entrada digital incluya código, QR y PDF válido.
def cuandoSeGeneraUnaEntradaDigital_debeIncluirQrCodigoYDocumentoPdf():
    # SimpleNamespace aporta los atributos que lee el servicio sin crear modelos,
    # guardar registros ni conectarse a la base de datos.
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

    # El servicio debe entregar exactamente los tres componentes de una entrada digital.
    assert set(resultado) == {
        "emergency_code",
        "qr_image_base64",
        "pdf_document_base64",
    }
    assert len(resultado["emergency_code"]) == 8
    # El QR se entrega como URI de datos para poder incrustarlo directamente como imagen.
    assert resultado["qr_image_base64"].startswith("data:image/png;base64,")
    # Se decodifica el documento Base64 y se valida su firma binaria (%PDF-).
    pdf = base64.b64decode(resultado["pdf_document_base64"])
    assert pdf.startswith(b"%PDF-")
