"""
INTEGRANTE 4 — Laura: gestión de eventos, zonas y tipos de entrada (15 pruebas)

Código bajo prueba (service-events/events/):
  - models.py      -> Event.is_upcoming, Event.is_full
  - models.py      -> TicketType.configured_seats, available_capacity, is_available
  - serializers.py -> EventSerializer.get_disponibilidad
  - serializers.py -> TicketTypeCreateSerializer.validate y validadores de campos

Las pruebas son unitarias: no guardan modelos, no usan PostgreSQL, Docker ni HTTP.
Cada prueba muestra explícitamente el patrón AAA:
  1) PREPARACIÓN (Arrange)  2) LÓGICA (Act)  3) VERIFICACIÓN (Assert)
"""

from datetime import timedelta
from types import SimpleNamespace

import pytest
from django.utils import timezone
from rest_framework import serializers

from events.models import Event, TicketType
from events.serializers import EventSerializer, TicketTypeCreateSerializer


class _TiposEntradaFalsos:
    """Sustituye el related manager de Django sin consultar la base de datos."""

    def __init__(self, vendidos):
        self._tipos = [SimpleNamespace(current_sold=cantidad) for cantidad in vendidos]

    def all(self):
        return self._tipos


class _ComprasFiltradasFalsas:
    def __init__(self, total):
        self._total = total

    def aggregate(self, **_kwargs):
        return {"total": self._total}


class _ComprasFalsas:
    """Simula purchase_set y registra el filtro aplicado por la regla de capacidad."""

    def __init__(self, total):
        self._total = total
        self.estados_filtrados = None

    def filter(self, **kwargs):
        self.estados_filtrados = kwargs["status__in"]
        return _ComprasFiltradasFalsas(self._total)


def cuandoEventoEsHoy_isUpcomingDebeRetornarVerdadero():
    # 1) PREPARACIÓN (Arrange)
    evento = SimpleNamespace(event_date=timezone.now().date())

    # 2) LÓGICA (Act)
    resultado = Event.is_upcoming.fget(evento)

    # 3) VERIFICACIÓN (Assert)
    assert resultado is True


def cuandoFechaDelEventoYaPaso_isUpcomingDebeRetornarFalso():
    # 1) PREPARACIÓN (Arrange)
    evento = SimpleNamespace(event_date=timezone.now().date() - timedelta(days=1))

    # 2) LÓGICA (Act)
    resultado = Event.is_upcoming.fget(evento)

    # 3) VERIFICACIÓN (Assert)
    assert resultado is False


def cuandoVentasIgualanLaCapacidad_isFullDebeRetornarVerdadero():
    # 1) PREPARACIÓN (Arrange)
    evento = SimpleNamespace(
        capacity=100,
        ticket_types=_TiposEntradaFalsos([35, 65]),
    )

    # 2) LÓGICA (Act)
    resultado = Event.is_full.fget(evento)

    # 3) VERIFICACIÓN (Assert)
    assert resultado is True


def cuandoVentasNoAlcanzanLaCapacidad_isFullDebeRetornarFalso():
    # 1) PREPARACIÓN (Arrange)
    evento = SimpleNamespace(
        capacity=100,
        ticket_types=_TiposEntradaFalsos([20, 79]),
    )

    # 2) LÓGICA (Act)
    resultado = Event.is_full.fget(evento)

    # 3) VERIFICACIÓN (Assert)
    assert resultado is False


def cuandoSeConsultaDisponibilidad_eventSerializerDebeRespetarElEstadoYCapacidad():
    # 1) PREPARACIÓN (Arrange)
    serializador = EventSerializer()
    borrador = SimpleNamespace(status="draft", capacity=100)
    publicado = SimpleNamespace(status="published", capacity=100)
    agotado = SimpleNamespace(status="published", capacity=0)

    # 2) LÓGICA (Act)
    resultados = [
        serializador.get_disponibilidad(borrador),
        serializador.get_disponibilidad(publicado),
        serializador.get_disponibilidad(agotado),
    ]

    # 3) VERIFICACIÓN (Assert)
    assert resultados == ["No disponible", "Disponible", "Agotado"]


def cuandoZonaTieneFilasYAsientos_configuredSeatsDebeMultiplicarlos():
    # 1) PREPARACIÓN (Arrange)
    zona = SimpleNamespace(seat_rows=5, seats_per_row=12)

    # 2) LÓGICA (Act)
    resultado = TicketType.configured_seats.fget(zona)

    # 3) VERIFICACIÓN (Assert)
    assert resultado == 60


def cuandoZonaNoTieneDistribucionCompleta_configuredSeatsDebeRetornarNinguno():
    # 1) PREPARACIÓN (Arrange)
    zona = SimpleNamespace(seat_rows=5, seats_per_row=None)

    # 2) LÓGICA (Act)
    resultado = TicketType.configured_seats.fget(zona)

    # 3) VERIFICACIÓN (Assert)
    assert resultado is None


def cuandoHayComprasActivasYPendientes_availableCapacityDebeRestarlas():
    # 1) PREPARACIÓN (Arrange)
    compras = _ComprasFalsas(total=23)
    zona = SimpleNamespace(max_capacity=100, purchase_set=compras)

    # 2) LÓGICA (Act)
    resultado = TicketType.available_capacity.fget(zona)

    # 3) VERIFICACIÓN (Assert)
    assert resultado == 77
    assert compras.estados_filtrados == ["active", "pending"]


def cuandoZonaActivaTieneCupo_isAvailableDebeRetornarVerdadero():
    # 1) PREPARACIÓN (Arrange)
    zona = SimpleNamespace(status="active", available_capacity=1)

    # 2) LÓGICA (Act)
    resultado = TicketType.is_available.fget(zona)

    # 3) VERIFICACIÓN (Assert)
    assert resultado is True


def cuandoZonaEstaInactivaAunqueTengaCupo_isAvailableDebeRetornarFalso():
    # 1) PREPARACIÓN (Arrange)
    zona = SimpleNamespace(status="inactive", available_capacity=50)

    # 2) LÓGICA (Act)
    resultado = TicketType.is_available.fget(zona)

    # 3) VERIFICACIÓN (Assert)
    assert resultado is False


def cuandoFilasPorAsientosCoincidenConCapacidad_validateDebeAceptarDistribucion():
    # 1) PREPARACIÓN (Arrange)
    datos = {
        "max_capacity": 50,
        "seat_rows": 5,
        "seats_per_row": 10,
        "zone_type": "general",
        "is_vip": False,
    }
    serializador = TicketTypeCreateSerializer(
        context={"request": SimpleNamespace(data=datos)}
    )

    # 2) LÓGICA (Act)
    resultado = serializador.validate(datos.copy())

    # 3) VERIFICACIÓN (Assert)
    assert resultado["max_capacity"] == 50
    assert resultado["is_vip"] is False


def cuandoDistribucionNoCoincideConCapacidad_validateDebeLanzarError():
    # 1) PREPARACIÓN (Arrange)
    datos = {"max_capacity": 50, "seat_rows": 4, "seats_per_row": 10}
    serializador = TicketTypeCreateSerializer(
        context={"request": SimpleNamespace(data=datos)}
    )

    # 2) LÓGICA (Act)
    with pytest.raises(serializers.ValidationError) as error:
        serializador.validate(datos.copy())

    # 3) VERIFICACIÓN (Assert)
    assert "debe coincidir exactamente" in str(error.value.detail)


def cuandoSoloSeEnviaCantidadDeFilas_validateDebeExigirAmbosCampos():
    # 1) PREPARACIÓN (Arrange)
    datos = {"max_capacity": 50, "seat_rows": 5}
    serializador = TicketTypeCreateSerializer(
        context={"request": SimpleNamespace(data=datos)}
    )

    # 2) LÓGICA (Act)
    with pytest.raises(serializers.ValidationError) as error:
        serializador.validate(datos.copy())

    # 3) VERIFICACIÓN (Assert)
    assert "filas y asientos por fila juntos" in str(error.value.detail)


def cuandoCapacidadNuevaEsMenorQueVentas_validateDebeProtegerAsientosVendidos():
    # 1) PREPARACIÓN (Arrange)
    zona_existente = SimpleNamespace(
        max_capacity=100,
        current_sold=21,
        zone_type="general",
        is_vip=False,
        seat_rows=10,
        seats_per_row=10,
    )
    datos = {"max_capacity": 20}
    serializador = TicketTypeCreateSerializer(
        instance=zona_existente,
        partial=True,
        context={"request": SimpleNamespace(data=datos)},
    )

    # 2) LÓGICA (Act)
    with pytest.raises(serializers.ValidationError) as error:
        serializador.validate(datos.copy())

    # 3) VERIFICACIÓN (Assert)
    assert "ventas realizadas (21)" in str(error.value.detail)


def cuandoPrecioEsCero_validatePriceDebeRechazarlo():
    # 1) PREPARACIÓN (Arrange)
    serializador = TicketTypeCreateSerializer()

    # 2) LÓGICA (Act)
    with pytest.raises(serializers.ValidationError) as error:
        serializador.validate_price(0)

    # 3) VERIFICACIÓN (Assert)
    assert "mayor a 0" in str(error.value.detail[0])
