"""Configuração da API, lida das variáveis de ambiente e do arquivo .env da raiz.

Variáveis já definidas no terminal têm prioridade sobre o .env.
"""

from __future__ import annotations

import os
import secrets
import warnings
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
MODOS = {"auto", "mock", "modelo"}


@dataclass(frozen=True)
class Configuracao:
    modo_preditor: str
    pasta_modelo: Path
    caminho_amostra: Path
    url_banco: str
    segredo_jwt: str
    horas_token: int
    admin_email: str
    admin_senha: str
    admin_nome: str


def _caminho(variavel: str, padrao: Path) -> Path:
    valor = os.getenv(variavel)
    if not valor:
        return padrao
    caminho = Path(valor)
    return caminho if caminho.is_absolute() else RAIZ / caminho


def carregar_configuracao() -> Configuracao:
    load_dotenv(RAIZ / ".env", override=False)
    modo = os.getenv("MODO_PREDITOR", "auto").strip().lower()
    if modo not in MODOS:
        raise ValueError(f"MODO_PREDITOR inválido: {modo!r}. Use um de: {', '.join(sorted(MODOS))}.")
    return Configuracao(
        modo_preditor=modo,
        pasta_modelo=_caminho("PASTA_MODELO", RAIZ / "models"),
        caminho_amostra=_caminho("CAMINHO_AMOSTRA", RAIZ / "data" / "amostra_enem_2023.parquet"),
        url_banco=url_banco(),
        segredo_jwt=_segredo_jwt(),
        horas_token=int(os.getenv("HORAS_TOKEN", "8")),
        admin_email=os.getenv("ADMIN_EMAIL", "coordenacao@edupredict.dev").strip().lower(),
        admin_senha=os.getenv("ADMIN_SENHA", "edupredict123"),
        admin_nome=os.getenv("ADMIN_NOME", "Coordenação pedagógica"),
    )


def url_banco() -> str:
    """DATABASE_URL (ex.: Postgres do Render) ou, sem ela, um SQLite local em data/edupredict.db."""
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        return f"sqlite:///{RAIZ / 'data' / 'edupredict.db'}"
    # O Render e o Heroku entregam "postgres://"; o SQLAlchemy com psycopg 3 espera "postgresql+psycopg://".
    for prefixo in ("postgres://", "postgresql://"):
        if url.startswith(prefixo):
            return "postgresql+psycopg://" + url.removeprefix(prefixo)
    return url


def _segredo_jwt() -> str:
    segredo = os.getenv("JWT_SECRET", "").strip()
    if segredo:
        return segredo
    warnings.warn(
        "JWT_SECRET não definido: usando um segredo temporário (os logins caem quando a API reinicia).",
        stacklevel=2,
    )
    return secrets.token_urlsafe(32)


def pasta_front() -> Path:
    """Pasta com o build do front (npm run build). Se existir, a própria API serve o site."""
    load_dotenv(RAIZ / ".env", override=False)
    return _caminho("PASTA_FRONT", RAIZ / "web" / "dist")
