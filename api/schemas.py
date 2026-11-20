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
CodigoCorRaca = Literal[0, 1, 2, 3, 4, 5]  # 0 = não declarada (dicionário ENEM 2023)
CodigoSexo = Literal["F", "M"]
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
    cor_raca: CodigoCorRaca | None = Field(
        default=None, description="Cor/raça autodeclarada. Ausente = não declarada (0)."
    )
    sexo: CodigoSexo | None = Field(default=None, description="Sexo (F/M), como no ENEM. Opcional.")
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
    tipo: Literal["acao", "contexto"] = Field(
        default="acao",
        description=(
            "acao: a escola ou a família podem atuar (internet, computador, reforço...). "
            "contexto: característica que o aluno não muda (cor/raça, sexo, região); não deve rotular o aluno."
        ),
    )


class Previsao(BaseModel):
    probabilidade_risco: float = Field(ge=0, le=1)
    nivel_risco: NivelRisco
    fatores: list[Fator]
    acompanhamento_recomendado: bool | None = Field(
        default=None,
        description=(
            "Se o aluno passa do limiar de acompanhamento. O limiar é ajustado por cor/raça para que todos os "
            "grupos tenham o mesmo recall (ver docs/resultados). None quando o modelo não informa limiar."
        ),
    )
    modelo: str = Field(description="Nome/versão do modelo que gerou a previsão ('mock' enquanto não houver modelo).")


# ---------------------------------------------------------------------------
# POST /api/prever/lote
# ---------------------------------------------------------------------------
MAX_LOTE = 1000


class LoteRequisicao(BaseModel):
    """Vários alunos de uma vez. Cada item é um perfil (mesmos campos de /api/prever) e pode ter um
    "identificador" livre (ex.: número de chamada). Itens inválidos voltam com erro, sem derrubar o lote."""

    alunos: list[dict] = Field(min_length=1, max_length=MAX_LOTE)


class ResultadoLote(BaseModel):
    linha: int = Field(description="Posição do aluno na lista enviada, começando em 1.")
    identificador: str | None = None
    probabilidade_risco: float | None = None
    nivel_risco: NivelRisco | None = None
    acompanhamento_recomendado: bool | None = None
    erro: str | None = None


class RespostaLote(BaseModel):
    resultados: list[ResultadoLote]
    modelo: str


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


class Comparacao(BaseModel):
    """Risco previsto (%) e média das notas do estado e do Brasil, na mesma amostra."""

    percentual_risco_uf: float
    percentual_risco_brasil: float
    media_uf: float
    media_brasil: float


class RiscoPorRede(BaseModel):
    rede_escola: int = Field(description="1 federal, 2 estadual, 3 municipal, 4 privada, 0 não informada")
    rotulo: str
    total_alunos: int
    percentual_risco: float
    media: float


class AnaliseMunicipio(BaseModel):
    municipio: str
    uf: str
    estatisticas_gerais: EstatisticasMunicipio
    escolas: list[EscolaResumo]
    comparacao: Comparacao | None = None
    por_rede: list[RiscoPorRede] = Field(default_factory=list)
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
