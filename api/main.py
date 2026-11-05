"""API do projeto ABP – Predição de desempenho no ENEM.

Rodar localmente:  uvicorn api.main:app --reload --port 8000
Documentação interativa: http://127.0.0.1:8000/docs
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .opcoes import montar_opcoes
from .schemas import AnaliseMunicipio, MunicipioRequisicao, OpcoesFormulario, PerfilAluno, Previsao
from .servico import criar_preditor


def _usar_mock() -> bool:
    return os.getenv("USAR_MOCK", "true").strip().lower() not in {"false", "0", "nao", "não"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.preditor = criar_preditor(usar_mock=_usar_mock())
    app.state.opcoes = montar_opcoes()
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


@app.get("/api/opcoes", response_model=OpcoesFormulario)
def opcoes() -> OpcoesFormulario:
    return app.state.opcoes


@app.post("/api/prever", response_model=Previsao)
def prever(perfil: PerfilAluno) -> Previsao:
    return app.state.preditor.prever(perfil)


@app.post("/api/municipios/analytics", response_model=AnaliseMunicipio)
def analisar_municipio(requisicao: MunicipioRequisicao) -> AnaliseMunicipio:
    return app.state.preditor.analisar_municipio(requisicao.municipio.strip(), requisicao.uf)
