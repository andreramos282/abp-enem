"""Regras de negócio compartilhadas pelo modelo real e pelo mock."""

from __future__ import annotations

from ml import colunas_2023 as c

from .schemas import NivelRisco, PerfilAluno

LIMITE_ALTO = 0.50
LIMITE_MEDIO = 0.25


def classificar(probabilidade: float) -> NivelRisco:
    """Converte a probabilidade de risco em nível (alto ≥ 50%, médio ≥ 25%)."""
    if probabilidade >= LIMITE_ALTO:
        return "alto"
    if probabilidade >= LIMITE_MEDIO:
        return "medio"
    return "baixo"


def status_escola(percentual_risco: float) -> str:
    """Nível de alerta da escola pelo % de alunos classificados em risco."""
    if percentual_risco >= LIMITE_ALTO * 100:
        return "ALTO_RISCO"
    if percentual_risco >= LIMITE_MEDIO * 100:
        return "MEDIO_RISCO"
    return "BAIXO_RISCO"


def renda_per_capita(perfil: PerfilAluno) -> float:
    """Renda per capita aproximada (meio da faixa de renda dividido pelas pessoas da casa)."""
    return c.RENDA_VALOR_MEDIO[perfil.renda_familiar] / perfil.pessoas_residencia
