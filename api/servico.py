"""Escolha do preditor usado pela API.

- `PreditorModelo` (api/modelo.py): usa models/pipeline.pkl, gerado por `python -m ml.treinar`.
- `PreditorMock` (api/mock.py): dados simulados, usados enquanto não há modelo treinado.

A escolha é feita pela variável MODO_PREDITOR (ver .env.example e api/config.py).
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from .schemas import AnaliseMunicipio, PerfilAluno, Previsao
from .traducoes import Idioma


class Preditor(Protocol):
    nome: str

    def prever(self, perfil: PerfilAluno, idioma: Idioma = "pt") -> Previsao: ...

    def analisar_municipio(self, municipio: str, uf: str) -> AnaliseMunicipio: ...


def existe_modelo(pasta_modelo: Path) -> bool:
    return (pasta_modelo / "pipeline.pkl").is_file() and (pasta_modelo / "metadados.json").is_file()


def criar_preditor(modo: str, pasta_modelo: Path, caminho_amostra: Path | None = None) -> Preditor:
    """modo: "mock" (dados simulados), "modelo" (exige o modelo treinado) ou "auto" (modelo se existir)."""
    if modo == "mock" or (modo == "auto" and not existe_modelo(pasta_modelo)):
        from .mock import PreditorMock

        return PreditorMock()
    if not existe_modelo(pasta_modelo):
        raise RuntimeError(f"Modelo não encontrado em {pasta_modelo}/. Rode: python -m ml.treinar")
    from .modelo import PreditorModelo

    return PreditorModelo(pasta_modelo, caminho_amostra)
