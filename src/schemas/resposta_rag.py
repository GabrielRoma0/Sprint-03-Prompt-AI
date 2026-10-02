"""
Schema de saída do pipeline RAG — Sprint 04.

Diferente de `ConsultaRecarga` (Sprint 03, dados operacionais simulados),
este schema é para perguntas respondidas com base na base de conhecimento
vetorizada (manuais, regimentos, FAQs, tabelas tarifárias). Exige citação
de fonte em toda resposta grounded (§3, item 3 do enunciado).
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class RespostaRAG(BaseModel):
    """Saída estruturada de uma consulta RAG, com citação obrigatória de fonte."""

    resposta: str = Field(
        ...,
        description="Resposta em linguagem natural, baseada apenas no contexto recuperado.",
    )
    respondeu_com_contexto: bool = Field(
        ...,
        description=(
            "False quando o contexto recuperado não cobre a pergunta e o "
            "modelo recusou responder em vez de inventar — nesse caso "
            "`fontes` deve ficar vazio e `resposta` deve ser a recusa."
        ),
    )
    # Declarado depois de respondeu_com_contexto: o field_validator abaixo
    # lê esse valor via info.data, que só contém campos já validados na
    # ordem de declaração do modelo.
    fontes: list[str] = Field(
        default_factory=list,
        description=(
            "Documento(s)/seção(ões) usados para montar a resposta, ex.: "
            "'manual_chargegrid.pdf, p.4'. Vazio apenas quando "
            "respondeu_com_contexto=False."
        ),
    )

    @field_validator("fontes")
    @classmethod
    def fontes_nao_vazias_quando_grounded(cls, v: list[str], info) -> list[str]:
        """Se respondeu com contexto, precisa citar ao menos uma fonte."""
        respondeu = info.data.get("respondeu_com_contexto")
        if respondeu and not v:
            raise ValueError(
                "respondeu_com_contexto=True mas nenhuma fonte foi citada — "
                "toda resposta grounded precisa citar documento/seção."
            )
        return v
