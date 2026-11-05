"""Contrato da API: formatos de entrada e saída (validados pelo Pydantic).

Qualquer mudança aqui precisa ser combinada com o front-end e registrada
em docs/api.md.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ml import colunas_2023 as c

CodigoEscolaridade = Literal["A", "B", "C", "D", "E", "F", "G", "H"]
CodigoOcupacao = Literal["A", "B", "C", "D", "E", "F"]
CodigoRenda = Literal["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q"]
CodigoComputador = Literal["A", "B", "C", "D", "E"]
CodigoInternet = Literal["A", "B"]
NivelRisco = Literal["alto", "medio", "baixo"]


# ---------------------------------------------------------------------------
# POST /api/prever
# ---------------------------------------------------------------------------
class PerfilAluno(BaseModel):
    """Perfil socioeconômico e escolar de um aluno (sem nenhuma nota)."""

    model_config = ConfigDict(extra="forbid")

    escolaridade_pai: CodigoEscolaridade
    escolaridade_mae: CodigoEscolaridade
    ocupacao_pai: CodigoOcupacao
    ocupacao_mae: CodigoOcupacao
    pessoas_residencia: int = Field(ge=1, le=20)
    renda_familiar: CodigoRenda
    computador: CodigoComputador
    internet: CodigoInternet
    tipo_escola: Literal[1, 2, 3]
    rede_escola: Literal[1, 2, 3, 4]
    localizacao_escola: Literal[1, 2]
    uf_escola: str = Field(min_length=2, max_length=2)
    faixa_etaria: int = Field(ge=1, le=20)
    bens: dict[str, str] = Field(
        default_factory=dict,
        description="Itens da casa (Q007 a Q023) e o código da resposta. Opcional.",
    )

    @field_validator("uf_escola")
    @classmethod
    def validar_uf(cls, valor: str) -> str:
        valor = valor.strip().upper()
        if valor not in c.UFS:
            raise ValueError(f"UF inválida: {valor}")
        return valor

    @field_validator("bens")
    @classmethod
    def validar_bens(cls, valor: dict[str, str]) -> dict[str, str]:
        invalidas = set(valor) - set(c.BENS)
        if invalidas:
            raise ValueError(f"Itens de bens desconhecidos: {sorted(invalidas)}")
        return {chave: str(resposta).strip().upper() for chave, resposta in valor.items()}


class Fator(BaseModel):
    variavel: str
    descricao: str
    impacto: float = Field(description="Pontos percentuais. Positivo aumenta o risco, negativo reduz.")


class Previsao(BaseModel):
    probabilidade_risco: float = Field(ge=0, le=1)
    nivel_risco: NivelRisco
    fatores: list[Fator]
    modelo: str = Field(description="Nome/versão do modelo que gerou a previsão ('mock' enquanto não houver modelo).")


# ---------------------------------------------------------------------------
# POST /api/municipios/analytics
# ---------------------------------------------------------------------------
class MunicipioRequisicao(BaseModel):
    municipio: str = Field(min_length=1, max_length=120)
    uf: str = Field(min_length=2, max_length=2)

    @field_validator("uf")
    @classmethod
    def validar_uf(cls, valor: str) -> str:
        valor = valor.strip().upper()
        if valor not in c.UFS:
            raise ValueError(f"UF inválida: {valor}")
        return valor


class EstatisticasMunicipio(BaseModel):
    total_alunos_avaliados: int
    total_escolas_unicas: int
    media_geral: float
    percentual_risco_municipio: float


class EscolaResumo(BaseModel):
    co_escola: int
    total_alunos_escola: int
    media_escola: float
    percentual_risco_escola: float
    status_alerta: Literal["ALTO_RISCO", "MEDIO_RISCO", "BAIXO_RISCO"]


class AnaliseMunicipio(BaseModel):
    municipio: str
    uf: str
    estatisticas_gerais: EstatisticasMunicipio
    escolas: list[EscolaResumo]
    modelo: str


# ---------------------------------------------------------------------------
# GET /api/opcoes
# ---------------------------------------------------------------------------
class Opcao(BaseModel):
    valor: str | int
    rotulo: str


class Campo(BaseModel):
    campo: str
    rotulo: str
    opcoes: list[Opcao]


class OpcoesFormulario(BaseModel):
    campos: list[Campo]
