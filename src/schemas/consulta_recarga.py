"""
Schema de domínio EV — GoodWe.

Representa a saída estruturada de uma consulta sobre um ponto de recarga
(estado do carregador, potência entregue e faturamento associado).

Aula 03 do Módulo 1: Structured Output com Pydantic v2.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class EstadoCarregador(str, Enum):
    """Estados possíveis de um carregador GoodWe."""

    DISPONIVEL = "disponivel"
    EM_CARGA = "em_carga"
    CONCLUIDO = "concluido"
    EM_FALHA = "em_falha"
    OFFLINE = "offline"


class ConsultaRecarga(BaseModel):
    """
    Saída estruturada para uma consulta de recarga de veículo elétrico.

    Esse é o schema que a chain LCEL (prompt | llm | parser) deve produzir
    e validar em `src/chain/builder.py`.
    """

    estado_carregador: EstadoCarregador = Field(
        ...,
        description="Estado atual do carregador no momento da consulta.",
    )
    potencia_kw: float | None = Field(
        default=None,
        description=(
            "Potência instantânea entregue pelo carregador, em kW. "
            "Use null se a conversa ainda não informou esse valor — "
            "nunca estime ou invente um número."
        ),
    )
    energia_entregue_kwh: float = Field(
        default=0.0,
        description="Energia total entregue na sessão de carga, em kWh.",
    )
    valor_faturado_brl: float = Field(
        default=0.0,
        description="Valor faturado para a sessão de carga, em reais (BRL).",
    )
    observacao: str | None = Field(
        default=None,
        description="Observação curta em linguagem natural sobre a consulta.",
    )

    @field_validator("potencia_kw")
    @classmethod
    def potencia_dentro_da_faixa(cls, v: float | None) -> float | None:
        """Carregadores residenciais/comerciais GoodWe operam tipicamente até 22 kW AC."""
        if v is None:
            return v
        if v < 0:
            raise ValueError("potencia_kw não pode ser negativa.")
        if v > 350:
            # Acima de 350 kW foge do catálogo GoodWe (DC ultra-rápido industrial).
            raise ValueError("potencia_kw fora da faixa esperada para o catálogo GoodWe (0–350 kW).")
        return round(v, 2)

    @field_validator("energia_entregue_kwh")
    @classmethod
    def energia_nao_negativa(cls, v: float) -> float:
        if v < 0:
            raise ValueError("energia_entregue_kwh não pode ser negativa.")
        return round(v, 2)

    @field_validator("valor_faturado_brl")
    @classmethod
    def faturamento_nao_negativo(cls, v: float) -> float:
        if v < 0:
            raise ValueError("valor_faturado_brl não pode ser negativo.")
        return round(v, 2)

    @field_validator("estado_carregador", mode="before")
    @classmethod
    def normalizar_estado(cls, v):
        """Aceita variações de texto (ex.: 'Em carga', 'EM_CARGA') e normaliza."""
        if isinstance(v, str):
            return v.strip().lower().replace(" ", "_")
        return v
