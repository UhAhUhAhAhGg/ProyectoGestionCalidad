"""
INTEGRANTE 1 — service-auth: validaciones de datos de usuario (15 pruebas unitarias)

Código bajo prueba (service-auth/users/):
  - serializers.py -> UserProfileSerializer.validate_phone()
  - serializers.py -> AdminCreateUserSerializer.validate()
  - models.py      -> UserProfile.full_name  y  UserManager.create_user()

Todas las pruebas siguen el patrón AAA:
  1) PREPARACIÓN (Arrange)  2) LÓGICA (Act)  3) VERIFICACIÓN (Assert)
"""
import pytest
from rest_framework import serializers

from users.models import User, UserProfile
from users.serializers import AdminCreateUserSerializer, UserProfileSerializer


# ──────────────────────────────────────────────────────────────────────────────
# Datos base reutilizables
# ──────────────────────────────────────────────────────────────────────────────
def _datos_comprador_validos():
    return {
        "email": "comprador@ticketgo.com",
        "password": "Segura123",
        "role_name": "Comprador",
        "first_name": "Ana",
    }


def _datos_promotor_validos():
    datos = _datos_comprador_validos()
    datos.update(
        {
            "email": "promotor@ticketgo.com",
            "role_name": "Promotor",
            "company_name": "Eventos Andinos SRL",
            "comercial_nit": "1023456022",
            "bank_account": "10000123456",
        }
    )
    return datos


# ══════════════════════════════════════════════════════════════════════════════
# UserProfileSerializer.validate_phone  (pruebas 1 a 5)
# ══════════════════════════════════════════════════════════════════════════════
def cuandoTelefonoSoloTieneDigitos_debeRetornarElMismoNumero():
    # 1) PREPARACIÓN
    serializador = UserProfileSerializer()
    telefono = "71234567"

    # 2) LÓGICA
    resultado = serializador.validate_phone(telefono)

    # 3) VERIFICACIÓN
    assert resultado == "71234567"


def cuandoTelefonoTieneEspacios_debeQuitarlosYRetornarNumeroLimpio():
    # 1) PREPARACIÓN
    serializador = UserProfileSerializer()
    telefono = "712 345 67"

    # 2) LÓGICA
    resultado = serializador.validate_phone(telefono)

    # 3) VERIFICACIÓN
    assert resultado == "71234567"


def cuandoTelefonoEmpiezaConMasYLuegoDigitos_debeAceptarloComoValido():
    # 1) PREPARACIÓN
    serializador = UserProfileSerializer()
    telefono = "+59171234567"

    # 2) LÓGICA
    resultado = serializador.validate_phone(telefono)

    # 3) VERIFICACIÓN
    assert resultado == "+59171234567"


def cuandoTelefonoContieneLetras_debeLanzarValidationError():
    # 1) PREPARACIÓN
    serializador = UserProfileSerializer()
    telefono = "7123abcd"

    # 2) LÓGICA
    with pytest.raises(serializers.ValidationError) as error:
        serializador.validate_phone(telefono)

    # 3) VERIFICACIÓN
    assert "solo debe contener números" in str(error.value.detail[0])


def cuandoTelefonoTieneMenosDeOchoDigitos_debeLanzarValidationErrorPorMuyCorto():
    # 1) PREPARACIÓN
    serializador = UserProfileSerializer()
    telefono = "1234567"  # 7 dígitos

    # 2) LÓGICA
    with pytest.raises(serializers.ValidationError) as error:
        serializador.validate_phone(telefono)

    # 3) VERIFICACIÓN
    assert "muy corto" in str(error.value.detail[0])


# ══════════════════════════════════════════════════════════════════════════════
# AdminCreateUserSerializer.validate  (pruebas 6 a 13)
# ══════════════════════════════════════════════════════════════════════════════
def cuandoPasswordTieneMenosDeOchoCaracteres_debeLanzarErrorEnCampoPassword():
    # 1) PREPARACIÓN
    serializador = AdminCreateUserSerializer()
    datos = _datos_comprador_validos()
    datos["password"] = "Ab1"

    # 2) LÓGICA
    with pytest.raises(serializers.ValidationError) as error:
        serializador.validate(datos)

    # 3) VERIFICACIÓN
    assert "al menos 8 caracteres" in str(error.value.detail["password"])


def cuandoPasswordNoTieneMayuscula_debeLanzarErrorEnCampoPassword():
    # 1) PREPARACIÓN
    serializador = AdminCreateUserSerializer()
    datos = _datos_comprador_validos()
    datos["password"] = "segura1234"

    # 2) LÓGICA
    with pytest.raises(serializers.ValidationError) as error:
        serializador.validate(datos)

    # 3) VERIFICACIÓN
    assert "mayúscula" in str(error.value.detail["password"])


def cuandoPasswordNoTieneNumero_debeLanzarErrorEnCampoPassword():
    # 1) PREPARACIÓN
    serializador = AdminCreateUserSerializer()
    datos = _datos_comprador_validos()
    datos["password"] = "SoloLetras"

    # 2) LÓGICA
    with pytest.raises(serializers.ValidationError) as error:
        serializador.validate(datos)

    # 3) VERIFICACIÓN
    assert "número" in str(error.value.detail["password"])


def cuandoDatosDeCompradorSonValidos_debeRetornarLosDatosSinErrores():
    # 1) PREPARACIÓN
    serializador = AdminCreateUserSerializer()
    datos = _datos_comprador_validos()

    # 2) LÓGICA
    resultado = serializador.validate(datos)

    # 3) VERIFICACIÓN
    assert resultado["email"] == "comprador@ticketgo.com"
    assert resultado["role_name"] == "Comprador"


def cuandoPromotorNoTieneNombreDeEmpresa_debeLanzarErrorEnCompanyName():
    # 1) PREPARACIÓN
    serializador = AdminCreateUserSerializer()
    datos = _datos_promotor_validos()
    datos["company_name"] = ""

    # 2) LÓGICA
    with pytest.raises(serializers.ValidationError) as error:
        serializador.validate(datos)

    # 3) VERIFICACIÓN
    assert "company_name" in error.value.detail


def cuandoPromotorNoTieneNitComercial_debeLanzarErrorEnComercialNit():
    # 1) PREPARACIÓN
    serializador = AdminCreateUserSerializer()
    datos = _datos_promotor_validos()
    datos["comercial_nit"] = ""

    # 2) LÓGICA
    with pytest.raises(serializers.ValidationError) as error:
        serializador.validate(datos)

    # 3) VERIFICACIÓN
    assert "comercial_nit" in error.value.detail


def cuandoPromotorNoTieneCuentaBancaria_debeLanzarErrorEnBankAccount():
    # 1) PREPARACIÓN
    serializador = AdminCreateUserSerializer()
    datos = _datos_promotor_validos()
    datos.pop("bank_account")

    # 2) LÓGICA
    with pytest.raises(serializers.ValidationError) as error:
        serializador.validate(datos)

    # 3) VERIFICACIÓN
    assert "bank_account" in error.value.detail


def cuandoDatosDePromotorEstanCompletos_debeRetornarLosDatosSinErrores():
    # 1) PREPARACIÓN
    serializador = AdminCreateUserSerializer()
    datos = _datos_promotor_validos()

    # 2) LÓGICA
    resultado = serializador.validate(datos)

    # 3) VERIFICACIÓN
    assert resultado["company_name"] == "Eventos Andinos SRL"
    assert resultado["comercial_nit"] == "1023456022"


# ══════════════════════════════════════════════════════════════════════════════
# Modelos de usuario  (pruebas 14 y 15)
# ══════════════════════════════════════════════════════════════════════════════
def cuandoPerfilTieneNombreYApellido_fullNameDebeConcatenarlosConUnEspacio():
    # 1) PREPARACIÓN
    perfil = UserProfile(first_name="Ana", last_name="Pérez")

    # 2) LÓGICA
    nombre_completo = perfil.full_name

    # 3) VERIFICACIÓN
    assert nombre_completo == "Ana Pérez"


def cuandoEmailEstaVacio_createUserDebeLanzarValueError():
    # 1) PREPARACIÓN
    email_vacio = ""

    # 2) LÓGICA
    with pytest.raises(ValueError) as error:
        User.objects.create_user(email=email_vacio, password="Segura123")

    # 3) VERIFICACIÓN
    assert "email es requerido" in str(error.value)
