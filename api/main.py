"""API do projeto ABP – Predição de desempenho no ENEM.

Rodar localmente:  uvicorn api.main:app --reload --port 8000
Documentação interativa: http://127.0.0.1:8000/docs
Se web/dist existir (npm run build), o site também é servido em http://127.0.0.1:8000/
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from .config import carregar_configuracao, pasta_front
from .opcoes import montar_opcoes
from .schemas import (
    AnaliseMunicipio,
    LoteRequisicao,
    MunicipioRequisicao,
    OpcoesFormulario,
    PerfilAluno,
    Previsao,
    RespostaLote,
    ResultadoLote,
)
from .servico import criar_preditor
from .traducoes import Idioma


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = carregar_configuracao()
    app.state.preditor = criar_preditor(config.modo_preditor, config.pasta_modelo, config.caminho_amostra)
    app.state.opcoes = {"pt": montar_opcoes("pt"), "en": montar_opcoes("en")}
    yield


app = FastAPI(
    title="ABP ENEM – API de risco de desempenho",
    version="0.1.0",
    lifespan=lifespan,
)

# Front-end do Vite em desenvolvimento.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "modelo": app.state.preditor.nome}


IdiomaQuery = Query("pt", description="Idioma dos textos da resposta: pt ou en.")


@app.get("/api/opcoes", response_model=OpcoesFormulario)
def opcoes(idioma: Idioma = IdiomaQuery) -> OpcoesFormulario:
    return app.state.opcoes[idioma]


@app.post("/api/prever", response_model=Previsao)
def prever(perfil: PerfilAluno, idioma: Idioma = IdiomaQuery) -> Previsao:
    return app.state.preditor.prever(perfil, idioma)


ERROS_LOTE = {
    "pt": {"faltando": "{campo}: não preenchido", "invalido": "{campo}: valor inválido ({valor})"},
    "en": {"faltando": "{campo}: missing", "invalido": "{campo}: invalid value ({valor})"},
}


def _erro_lote(erro: ValidationError, idioma: Idioma) -> str:
    textos = ERROS_LOTE[idioma]
    partes = []
    for e in erro.errors():
        campo = str(e["loc"][0]) if e["loc"] else "perfil"
        tipo = "faltando" if e["type"] == "missing" else "invalido"
        partes.append(textos[tipo].format(campo=campo, valor=e.get("input")))
    return "; ".join(dict.fromkeys(partes))


@app.post("/api/prever/lote", response_model=RespostaLote)
def prever_lote(requisicao: LoteRequisicao, idioma: Idioma = IdiomaQuery) -> RespostaLote:
    """Risco de vários alunos de uma vez (sem os fatores, para ser rápido)."""
    resultados: list[ResultadoLote] = []
    validos: list[tuple[int, PerfilAluno]] = []
    for linha, aluno in enumerate(requisicao.alunos, start=1):
        dados = dict(aluno)
        identificador = dados.pop("identificador", None)
        resultado = ResultadoLote(linha=linha, identificador=None if identificador is None else str(identificador))
        try:
            validos.append((len(resultados), PerfilAluno.model_validate(dados)))
        except ValidationError as erro:
            resultado.erro = _erro_lote(erro, idioma)
        resultados.append(resultado)

    if validos:
        previsoes = app.state.preditor.prever_lote([perfil for _, perfil in validos])
        for (posicao, _), previsao in zip(validos, previsoes, strict=True):
            resultados[posicao].probabilidade_risco = previsao.probabilidade_risco
            resultados[posicao].nivel_risco = previsao.nivel_risco
            resultados[posicao].acompanhamento_recomendado = previsao.acompanhamento_recomendado
    return RespostaLote(resultados=resultados, modelo=app.state.preditor.nome)


@app.post("/api/municipios/analytics", response_model=AnaliseMunicipio)
def analisar_municipio(requisicao: MunicipioRequisicao, idioma: Idioma = IdiomaQuery) -> AnaliseMunicipio:
    try:
        return app.state.preditor.analisar_municipio(requisicao.municipio.strip(), requisicao.uf, idioma)
    except LookupError as erro:
        raise HTTPException(status_code=404, detail=str(erro)) from erro


# Em produção (Docker), a API também entrega o front-end já compilado.
# Montado por último para não esconder as rotas /api e /docs.
if (front := pasta_front()).is_dir():
    app.mount("/", StaticFiles(directory=front, html=True), name="front")
