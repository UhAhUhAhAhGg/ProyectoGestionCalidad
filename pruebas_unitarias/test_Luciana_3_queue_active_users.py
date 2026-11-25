"""
INTEGRANTE 3 — service-queue: control de usuarios activos de la cola virtual (15 pruebas unitarias)

Código bajo prueba (service-queue/queue_app/):
  - active_users.py -> register_user_activity()
  - active_users.py -> remove_user_activity()
  - active_users.py -> get_active_users_count()
  - active_users.py -> is_user_active()
  - active_users.py -> clear_event_activity()
  - active_users.py -> _cleanup_expired()
  - models.py       -> SeatReservation.is_expired

Todas las pruebas siguen el patrón AAA:
  1) PREPARACIÓN (Arrange)  2) LÓGICA (Act)  3) VERIFICACIÓN (Assert)
"""
import time
from datetime import timedelta

import pytest

from django.utils import timezone

from queue_app import active_users
from queue_app.models import SeatReservation


# Preparación común: cada prueba empieza con la cola vacía
# (active_users guarda los datos en un diccionario global en memoria)
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def limpiar_sesiones_activas():
    active_users._active_sessions.clear()  # Se inicia la cola vacia 
    yield                                  # pytest ejecuta la prueba
    active_users._active_sessions.clear()  # DESPUÉS de la prueba: limpia lo que dejó


# ══════════════════════════════════════════════════════════════════════════════
# register_user_activity  (pruebas 1 a 3)
# ══════════════════════════════════════════════════════════════════════════════

# 1) Prueba que al registrar a un usuario en un evento que aún no existe, se cree ese evento con el usuario dentro
def cuandoSeRegistraUsuarioEnEventoNuevo_debeCrearElEventoConEseUsuario():
    # 1) PREPARACIÓN DE LA PRUEBA 
    evento = "evento-1"
    usuario = "usuario-1"

    # 2) LÓGICA: ejecutar el método bajo prueba
    active_users.register_user_activity(evento, usuario)

    # 3) VERIFICACIÓN: el evento se creó y contiene al usuario
    assert evento in active_users._active_sessions
    assert usuario in active_users._active_sessions[evento]

# 2) Prueba que al registrar al mismo usuario dos veces en la cola de un evento solo se cuente una vexz y no haya duplicados
def cuandoSeRegistraElMismoUsuarioDosVeces_debeContarseUnaSolaVez():
    # 1) PREPARACIÓN
    evento = "evento-1"
    usuario = "usuario-1"
    # 2) LÓGICA
    active_users.register_user_activity(evento, usuario)
    active_users.register_user_activity(evento, usuario) 
    # 3) VERIFICACIÓN
    assert active_users.get_active_users_count(evento) == 1  # solo se cuenta una vez 

# 3) Prueba que al registrar usuarios en eventos diferentes las colas no se mezclen y cada una tenga solo sus usuarios asignados
def cuandoSeRegistranUsuariosEnEventosDistintos_cadaEventoDebeTenerSoloSusUsuarios():
    # 1) PREPARACIÓN
    evento1= "evento-1"
    usuario1="usuario-1"
    evento2="evento-2"
    usuario2="usuario-2"
    # 2) LÓGICA
    active_users.register_user_activity(evento1, usuario1)
    active_users.register_user_activity(evento2, usuario2)
    # 3) VERIFICACIÓn
    # Cada usuario está activo en SU evento
    assert active_users.is_user_active(evento1, usuario1) == True
    assert active_users.is_user_active(evento2, usuario2) == True

    # Pero NO aparece en el evento del otro (las colas no se mezclan)
    assert active_users.is_user_active(evento1, usuario2) == False
    assert active_users.is_user_active(evento2, usuario1) == False


# ══════════════════════════════════════════════════════════════════════════════
# remove_user_activity  (pruebas 4 y 5)
# ══════════════════════════════════════════════════════════════════════════════

# 4) Prueba que cuando se remueve un usuario regstrado en un evento este deja de aparecer en la cola
def cuandoSeRemueveUsuarioRegistrado_debeDejarDeEstarActivo():
    # 1) PREPARACIÓN
    evento = "evento-1"
    usuario = "usuario-1"
    # 2) LÓGICA
    active_users.register_user_activity(evento, usuario)
    active_users.remove_user_activity(evento, usuario)

    # 3) VERIFICACIÓN
    assert active_users.get_active_users_count(evento) == 0 #n hay usuarios 

# 5) Prueba que cuando se intenta remover un usuario que no existe o en un evento que no existe el sistema no lance error
def cuandoSeRemueveUsuarioQueNoExiste_noDebeLanzarError():
    # 1) PREPARACIÓN
    evento = "evento-1"
    usuario = "usuario-1"
    # 2) LÓGICA 
    active_users.remove_user_activity(evento, usuario) 

    # 3) VERIFICACIÓN
    assert active_users.get_active_users_count(evento) == 0 #no hay usuarios, no se lanza error


# ══════════════════════════════════════════════════════════════════════════════
# get_active_users_count  (pruebas 6 a 8)
# ══════════════════════════════════════════════════════════════════════════════

# 6) Prueba que cuando un evento no tiene usuarios activos, se retorne 0 al consultar la cantidad de usuaris
def cuandoEventoNoTieneUsuarios_getActiveUsersCountDebeRetornarCero():
    # 1) PREPARACIÓN
    evento ="evento-1"

    # 2) LÓGICA
    cantidad = active_users.get_active_users_count(evento)
    # 3) VERIFICACIÓN
    assert cantidad == 0

# 7) Prueba que cuando hay varios usuarios registrados en un evento, la funcion retorne la cant correcta
def cuandoHayVariosUsuariosRegistrados_getActiveUsersCountDebeRetornarLaCantidad():
    # 1) PREPARACIÓN
    evento = "evento-1"
    usuarioA = "usuario-1"
    usuarioB = "usuario-2"
    usuarioC = "usuario-3"
    # 2) LÓGICA
    active_users.register_user_activity(evento, usuarioA)
    active_users.register_user_activity(evento, usuarioB)
    active_users.register_user_activity(evento, usuarioC)

    # 3) VERIFICACIÓN
    assert active_users.get_active_users_count(evento) == 3

# 8) Prueba que cuando se remueve a uno de varios usuarios, la cantidad de activos disminuye en uno
def cuandoSeRemueveUnoDeVariosUsuarios_getActiveUsersCountDebeDisminuirEnUno():
    # 1) PREPARACION
    evento = "evento-1"
    usuarioA = "usuario-1"
    usuarioB = "usuario-2"
    active_users.register_user_activity(evento, usuarioA)
    active_users.register_user_activity(evento, usuarioB)

    # 2) LÓGICA
    active_users.remove_user_activity(evento, usuarioA)
    cantidad = active_users.get_active_users_count(evento)

    # 3) VERIFICACIÓN
    assert cantidad == 1


# ══════════════════════════════════════════════════════════════════════════════
# is_user_active  (pruebas 9 a 11)
# ══════════════════════════════════════════════════════════════════════════════

# 9) Prueba que cuando un usuario esta registrado en un evento, la funcion debe retornar Verdadero
def cuandoUsuarioEstaRegistrado_isUserActiveDebeRetornarTrue():
    # 1) PREPARACIÓN
    usuario = "usuario-1"
    evento = "evento-1"
    active_users.register_user_activity(evento, usuario)
    # 2) LÓGICA
    is_active = active_users.is_user_active(evento, usuario)
    # 3) VERIFICACIÓN
    assert is_active == True

# 10) Prueba que si un usuario está activo en un evento que no existe (nadie se registró nunca en él), la función responde False.
def cuandoEventoNoExiste_isUserActiveDebeRetornarFalse():
    # 1) PREPARACIÓN
    usuario = "usuario-1"
    evento = "evento-1"
    # 2) LÓGICA
    resultado = active_users.is_user_active(evento, usuario)
    # 3) VERIFICACIÓN
    assert resultado == False 

# 11) Prueba que si un usuario estaba activo pero su tiempo expiro, la funcion debe retornar falso
def cuandoUsuarioExpiro_isUserActiveDebeRetornarFalse(monkeypatch):
    # 1) PREPARACIÓN
    evento = "evento-1"
    usuario = "usuario-1"
    active_users.register_user_activity(evento, usuario)

    tres_minutos_despues = time.time() + 3 * 60
    monkeypatch.setattr(active_users.time, "time", lambda: tres_minutos_despues)

    # 2) LÓGICA
    resultado = active_users.is_user_active(evento, usuario)

    # 3) VERIFICACIÓN: 
    assert resultado == False #pasaron mas de 2 minutos ya se expiro y no esta activo


# ══════════════════════════════════════════════════════════════════════════════
# clear_event_activity  (pruebas 12 y 13)
# ══════════════════════════════════════════════════════════════════════════════

# 12) Prueba que cuando se limpia un evento este se queda sin usuarios activos p.ej cuando se reconfigura
def cuandoSeLimpiaUnEvento_clearEventActivityDebeDejarloSinUsuarios():
    # 1) PREPARACIÓN
    evento = "evento-1"
    usuario = "usuario-1"
    active_users.register_user_activity(evento, usuario)
    # 2) LÓGICA
    active_users.clear_event_activity(evento)
    # 3) VERIFICACIÓN
    assert active_users.get_active_users_count(evento) == 0 #no hay usuarios activos

# 13) Prueba que al limpiar un evento, los usuarios de OTRO evento no se borran
def cuandoSeLimpiaUnEvento_clearEventActivityNoDebeAfectarAOtrosEventos():
    # 1) PREPARACIÓN
    evento1 = "evento-1"
    evento2 = "evento-2"
    active_users.register_user_activity(evento1, "usuario-1")
    active_users.register_user_activity(evento2, "usuario-2")

    # 2) LÓGICA
    active_users.clear_event_activity(evento1)

    # 3) VERIFICACIÓN
    assert active_users.get_active_users_count(evento1) == 0
    assert active_users.get_active_users_count(evento2) == 1


# ══════════════════════════════════════════════════════════════════════════════
# SeatReservation.is_expired  (pruebas 14 y 15)
# ══════════════════════════════════════════════════════════════════════════════

# 14) Prueba que una reserva de asiento que sigue activa pero ya pasó su hora límite se considera expirada
def cuandoReservaActivaPasoSuFechaDeExpiracion_isExpiredDebeRetornarTrue():
    # 1) PREPARACIÓN: reserva activa que venció hace 5 minutos 
    hace_5_minutos = timezone.now() - timedelta(minutes=5)
    reserva = SeatReservation(status="active", expires_at=hace_5_minutos)

    # 2) LÓGICA
    resultado = reserva.is_expired

    # 3) VERIFICACIÓN
    assert resultado == True #debe estar expirada 

# 15) Prueba que una reserva ya confirmada (pagada) no se considera expirada aunque haya pasado su hora límite
def cuandoReservaYaFueConfirmada_isExpiredDebeRetornarFalse():
    # 1) PREPARACIÓN: reserva confirmada que venció
    hace_5_minutos = timezone.now() - timedelta(minutes=5)
    reserva = SeatReservation(status="confirmed", expires_at=hace_5_minutos)

    # 2) LÓGICA: se consulta si la reserva expiró
    resultado = reserva.is_expired

    # 3) VERIFICACIÓN: al estar pagada, NO debe estar expirada
    assert resultado == False
