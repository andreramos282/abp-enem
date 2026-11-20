"""API do projeto ABP – Predição de desempenho no ENEM.

Rodar localmente:  uvicorn api.main:app --reload --port 8000
Documentação interativa: http://127.0.0.1:8000/docs
Se web/dist existir (npm run build), o site também é servido em http://127.0.0.1:8000/
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from sqlalchemy import delete, select

from .auth import conferir_senha, criar_token, ler_token
from .banco import Analise, Banco, Usuario
from .config import carregar_configuracao, pasta_front
from .opcoes import montar_opcoes
from .schemas import (
    AnaliseMunicipio,
    ItemHistorico,
    LoginRequisicao,
    LoteRequisicao,
    MunicipioRequisicao,
    OpcoesFormulario,
    PerfilAluno,
    Previsao,
    RespostaLogin,
    RespostaLote,
    ResultadoLote,
    UsuarioPublico,
)
from .servico import criar_preditor
from .traducoes import Idioma


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = carregar_configuracao()
    app.state.preditor = criar_preditor(
        config.modo_preditor, config.pasta_modelo, config.caminho_amostra, config.caminho_risco
    )
    app.state.opcoes = {"pt": montar_opcoes("pt"), "en": montar_opcoes("en")}
    app.state.config = config
    app.state.banco = Banco(config.url_banco)
    app.state.banco.criar_tabelas()
    app.state.banco.criar_usuario_inicial(config.admin_email, config.admin_senha, config.admin_nome)
    yield
    app.state.banco.engine.dispose()


app = FastAPI(
    title="ABP ENEM – API de risco de desempenho",
    version="0.1.0",
    lifespan=lifespan,
)

# Front-end do Vite em desenvolvimento.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "modelo": app.state.preditor.nome}


IdiomaQuery = Query("pt", description="Idioma dos textos da resposta: pt ou en.")
_bearer = HTTPBearer(auto_error=False)


def usuario_opcional(
    request: Request, credenciais: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]
) -> Usuario | None:
    """Usuário do token "Authorization: Bearer ...", ou None sem token (ou com token inválido)."""
    if credenciais is None:
        return None
    usuario_id = ler_token(credenciais.credentials, request.app.state.config.segredo_jwt)
    if usuario_id is None:
        return None
    with request.app.state.banco.abrir() as sessao:
        return sessao.get(Usuario, usuario_id)


def usuario_obrigatorio(usuario: Annotated[Usuario | None, Depends(usuario_opcional)]) -> Usuario:
    if usuario is None:
        raise HTTPException(status_code=401, detail="Faça login.", headers={"WWW-Authenticate": "Bearer"})
    return usuario


def _publico(usuario: Usuario) -> UsuarioPublico:
    return UsuarioPublico(id=usuario.id, nome=usuario.nome, email=usuario.email, cargo=usuario.cargo)


@app.post("/api/auth/login", response_model=RespostaLogin)
def login(requisicao: LoginRequisicao) -> RespostaLogin:
    with app.state.banco.abrir() as sessao:
        usuario = sessao.scalar(select(Usuario).where(Usuario.email == requisicao.email.strip().lower()))
    if usuario is None or not conferir_senha(requisicao.senha, usuario.senha_hash):
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.")
    config = app.state.config
    return RespostaLogin(
        token=criar_token(usuario.id, config.segredo_jwt, config.horas_token), usuario=_publico(usuario)
    )


@app.get("/api/auth/eu", response_model=UsuarioPublico)
def eu(usuario: Annotated[Usuario, Depends(usuario_obrigatorio)]) -> UsuarioPublico:
    return _publico(usuario)


@app.get("/api/historico", response_model=list[ItemHistorico])
def historico(
    usuario: Annotated[Usuario, Depends(usuario_obrigatorio)], limite: int = Query(50, ge=1, le=500)
) -> list[ItemHistorico]:
    """Análises do usuário logado, da mais recente para a mais antiga."""
    with app.state.banco.abrir() as sessao:
        analises = sessao.scalars(
            select(Analise)
            .where(Analise.usuario_id == usuario.id)
            .order_by(Analise.criado_em.desc(), Analise.id.desc())
            .limit(limite)
        ).all()
    return [ItemHistorico(id=a.id, criado_em=a.criado_em, perfil=a.perfil, previsao=a.previsao) for a in analises]


@app.delete("/api/historico/{analise_id}", status_code=204)
def apagar_analise(analise_id: int, usuario: Annotated[Usuario, Depends(usuario_obrigatorio)]) -> Response:
    with app.state.banco.abrir() as sessao:
        apagadas = sessao.execute(
            delete(Analise).where(Analise.id == analise_id, Analise.usuario_id == usuario.id)
        ).rowcount
        sessao.commit()
    if not apagadas:
        raise HTTPException(status_code=404, detail="Análise não encontrada.")
    return Response(status_code=204)


@app.get("/api/opcoes", response_model=OpcoesFormulario)
def opcoes(idioma: Idioma = IdiomaQuery) -> OpcoesFormulario:
    return app.state.opcoes[idioma]


@app.post("/api/prever", response_model=Previsao)
def prever(
    perfil: PerfilAluno,
    usuario: Annotated[Usuario | None, Depends(usuario_opcional)],
    idioma: Idioma = IdiomaQuery,
    salvar: bool = Query(True, description="Com login, guarda a análise no histórico (false: só calcula)."),
) -> Previsao:
    """Previsão de um aluno. Com login, a análise também vai para o histórico do usuário."""
    previsao = app.state.preditor.prever(perfil, idioma)
    if usuario is not None and salvar:
        with app.state.banco.abrir() as sessao:
            sessao.add(
                Analise(
                    usuario_id=usuario.id,
                    perfil=perfil.model_dump(mode="json"),
                    previsao=previsao.model_dump(mode="json"),
                    probabilidade=previsao.probabilidade_risco,
                    nivel=previsao.nivel_risco,
                    acompanhamento=previsao.acompanhamento_recomendado,
                    modelo=previsao.modelo,
                )
            )
            sessao.commit()
    return previsao


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
