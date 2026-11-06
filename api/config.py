"""Configuração da API, lida das variáveis de ambiente e do arquivo .env da raiz.

Variáveis já definidas no terminal têm prioridade sobre o .env.
"""

from __future__ import annotations

import os
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
    )


def pasta_front() -> Path:
    """Pasta com o build do front (npm run build). Se existir, a própria API serve o site."""
    load_dotenv(RAIZ / ".env", override=False)
    return _caminho("PASTA_FRONT", RAIZ / "web" / "dist")
