"""Domain vocabulary.

The Spanish names are deliberate: they are the terms brokers, advisors and
managers actually use, and keeping them in the model removes a translation
layer between the business and the schema. Enum *values* are the stable
contract stored in Postgres and exposed over the API.
"""

from __future__ import annotations

from enum import StrEnum


class TipoCliente(StrEnum):
    PERSONA = "persona"
    EMPRESA = "empresa"


class TipoDocumento(StrEnum):
    CC = "cc"
    CE = "ce"
    NIT = "nit"
    PASAPORTE = "pasaporte"
    TI = "ti"


class RolUsuario(StrEnum):
    ADMIN = "admin"
    GERENTE = "gerente"
    ASESOR = "asesor"


class Canal(StrEnum):
    """Where a person or a piece of information entered the platform."""

    WEB = "web"
    WHATSAPP = "whatsapp"
    TELEFONO = "telefono"
    PRESENCIAL = "presencial"
    REFERIDO = "referido"
    MANUAL = "manual"


class EstadoSolicitud(StrEnum):
    """Lifecycle of an inbound quote request (Módulo 2)."""

    NUEVA = "nueva"
    ASIGNADA = "asignada"
    EN_PROCESO = "en_proceso"
    CONVERTIDA = "convertida"
    DESCARTADA = "descartada"


class EtapaOportunidad(StrEnum):
    """Commercial pipeline. Ordered; see `EtapaOportunidad.orden`."""

    NUEVO = "nuevo"
    CONTACTADO = "contactado"
    COTIZANDO = "cotizando"
    PROPUESTA_ENVIADA = "propuesta_enviada"
    EN_NEGOCIACION = "en_negociacion"
    GANADO = "ganado"
    PERDIDO = "perdido"

    @property
    def orden(self) -> int:
        return _ORDEN_ETAPAS[self]

    @property
    def es_terminal(self) -> bool:
        return self in (EtapaOportunidad.GANADO, EtapaOportunidad.PERDIDO)


_ORDEN_ETAPAS: dict[EtapaOportunidad, int] = {
    EtapaOportunidad.NUEVO: 0,
    EtapaOportunidad.CONTACTADO: 1,
    EtapaOportunidad.COTIZANDO: 2,
    EtapaOportunidad.PROPUESTA_ENVIADA: 3,
    EtapaOportunidad.EN_NEGOCIACION: 4,
    EtapaOportunidad.GANADO: 5,
    EtapaOportunidad.PERDIDO: 5,
}


class MotivoPerdida(StrEnum):
    PRECIO = "precio"
    COMPETENCIA = "competencia"
    SIN_RESPUESTA = "sin_respuesta"
    NO_ASEGURABLE = "no_asegurable"
    DESISTE = "desiste"
    OTRO = "otro"


class EstadoCotizacion(StrEnum):
    BORRADOR = "borrador"
    ENVIADA = "enviada"
    ACEPTADA = "aceptada"
    RECHAZADA = "rechazada"
    VENCIDA = "vencida"


class EstadoPoliza(StrEnum):
    VIGENTE = "vigente"
    PROXIMA_A_VENCER = "proxima_a_vencer"
    VENCIDA = "vencida"
    RENOVADA = "renovada"
    CANCELADA = "cancelada"


class EstadoRenovacion(StrEnum):
    PENDIENTE = "pendiente"
    EN_GESTION = "en_gestion"
    COMPLETADA = "completada"
    OMITIDA = "omitida"


class DireccionComunicacion(StrEnum):
    ENTRANTE = "entrante"
    SALIENTE = "saliente"


class TipoCampo(StrEnum):
    """Field types available to a ramo's dynamic quote form (Módulo 2)."""

    TEXTO = "texto"
    NUMERO = "numero"
    ENTERO = "entero"
    EMAIL = "email"
    TELEFONO = "telefono"
    FECHA = "fecha"
    SELECCION = "seleccion"
    MULTISELECCION = "multiseleccion"
    BOOLEANO = "booleano"
    DOCUMENTO = "documento"
    PLACA = "placa"


class NivelRiesgo(StrEnum):
    BAJO = "bajo"
    MEDIO = "medio"
    ALTO = "alto"


class VentanaVencimiento(StrEnum):
    """Renewal dashboard buckets (Módulo 6, §15 of the platform brief)."""

    CRITICA = "critica"  # <= 7 días
    URGENTE = "urgente"  # 8 - 15 días
    PROXIMA = "proxima"  # 16 - 30 días
    PLANIFICADA = "planificada"  # 31 - 60 días
    FUTURA = "futura"  # > 60 días
    VENCIDA = "vencida"  # already expired

    @classmethod
    def desde_dias(cls, dias: int) -> VentanaVencimiento:
        """Classify a policy by days remaining until expiry."""
        if dias < 0:
            return cls.VENCIDA
        if dias <= 7:
            return cls.CRITICA
        if dias <= 15:
            return cls.URGENTE
        if dias <= 30:
            return cls.PROXIMA
        if dias <= 60:
            return cls.PLANIFICADA
        return cls.FUTURA
