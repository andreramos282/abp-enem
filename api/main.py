"""API do projeto ABP – Predição de desempenho no ENEM.

Rodar localmente:  uvicorn api.main:app --reload --port 8000
Documentação interativa: http://127.0.0.1:8000/docs
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .opcoes import montar_opcoes
from .schemas import AnaliseMunicipio, MunicipioRequisicao, OpcoesFormulario, PerfilAluno, Previsao
from .servico import criar_preditor
from .traducoes import Idioma


RAIZ = Path(__file__).resolve().parent.parent


def _modo() -> str:
    modo = os.getenv("MODO_PREDITOR", "auto").strip().lower()
    return modo if modo in {"auto", "mock", "modelo"} else "auto"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.preditor = criar_preditor(
        _modo(),
        pasta_modelo=Path(os.getenv("PASTA_MODELO", RAIZ / "models")),
        caminho_amostra=Path(os.getenv("CAMINHO_AMOSTRA", RAIZ / "data" / "amostra_enem_2023.parquet")),
    )
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


@app.post("/api/municipios/analytics", response_model=AnaliseMunicipio)
def analisar_municipio(requisicao: MunicipioRequisicao) -> AnaliseMunicipio:
    try:
        return app.state.preditor.analisar_municipio(requisicao.municipio.strip(), requisicao.uf)
    except LookupError as erro:
        raise HTTPException(status_code=404, detail=str(erro)) from erro
