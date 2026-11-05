"""Lógica de previsão.

Enquanto o modelo da Sprint 3 não fica pronto, a API usa o `PreditorMock`:
uma regra simples e determinística que devolve respostas no formato final,
para o front-end já poder ser desenvolvido. Os valores NÃO vêm de modelo
treinado e não devem ser usados como resultado do projeto.

Para ligar o modelo real, implemente `PreditorModelo` (carregando
models/pipeline.pkl) e defina USAR_MOCK=false.
"""

from __future__ import annotations

import hashlib
import math
from typing import Protocol

from ml import colunas_2023 as c

from .schemas import (
    AnaliseMunicipio,
    EscolaResumo,
    EstatisticasMunicipio,
    Fator,
    NivelRisco,
    PerfilAluno,
    Previsao,
)

LIMITE_ALTO = 0.50
LIMITE_MEDIO = 0.25


def classificar(probabilidade: float) -> NivelRisco:
    if probabilidade >= LIMITE_ALTO:
        return "alto"
    if probabilidade >= LIMITE_MEDIO:
        return "medio"
    return "baixo"


def renda_per_capita(perfil: PerfilAluno) -> float:
    return c.RENDA_VALOR_MEDIO[perfil.renda_familiar] / perfil.pessoas_residencia


class Preditor(Protocol):
    nome: str

    def prever(self, perfil: PerfilAluno) -> Previsao: ...

    def analisar_municipio(self, municipio: str, uf: str) -> AnaliseMunicipio: ...


class PreditorMock:
    """Respostas simuladas e determinísticas (o mesmo perfil sempre gera o mesmo resultado)."""

    nome = "mock"

    _ESCOLARIDADE_PESO = {"A": 0.9, "B": 0.7, "C": 0.5, "D": 0.3, "E": 0.0, "F": -0.5, "G": -0.7, "H": 0.3}

    def prever(self, perfil: PerfilAluno) -> Previsao:
        rpc = renda_per_capita(perfil)
        contribuicoes: list[tuple[str, str, float]] = [
            ("renda_per_capita", f"Renda per capita de aproximadamente R$ {rpc:,.0f}".replace(",", "."),
             0.8 * (3.2 - math.log10(rpc + 50))),
            ("escolaridade_mae", f"Escolaridade da mãe: {c.ESCOLARIDADE[perfil.escolaridade_mae].lower()}",
             self._ESCOLARIDADE_PESO[perfil.escolaridade_mae]),
            ("escolaridade_pai", f"Escolaridade do pai: {c.ESCOLARIDADE[perfil.escolaridade_pai].lower()}",
             0.6 * self._ESCOLARIDADE_PESO[perfil.escolaridade_pai]),
            ("computador", "Não possui computador em casa" if perfil.computador == "A" else "Possui computador em casa",
             0.45 if perfil.computador == "A" else -0.25),
            ("internet", "Sem acesso à internet em casa" if perfil.internet == "A" else "Possui acesso à internet em casa",
             0.4 if perfil.internet == "A" else -0.15),
            ("rede_escola", f"Rede da escola: {c.REDE_ESCOLA[perfil.rede_escola].lower()}",
             {1: -0.6, 2: 0.35, 3: 0.4, 4: -0.7}[perfil.rede_escola]),
            ("localizacao_escola", f"Escola em área {c.LOCALIZACAO_ESCOLA[perfil.localizacao_escola].lower()}",
             0.3 if perfil.localizacao_escola == 2 else 0.0),
            ("faixa_etaria", f"Faixa etária: {c.FAIXA_ETARIA[perfil.faixa_etaria].lower()}",
             0.25 * max(0, perfil.faixa_etaria - 3)),
        ]

        logito = -1.5 + sum(valor for _, _, valor in contribuicoes)
        probabilidade = 1 / (1 + math.exp(-logito))

        # Impacto aproximado de cada fator, em pontos percentuais.
        derivada = probabilidade * (1 - probabilidade) * 100
        fatores = [
            Fator(variavel=variavel, descricao=descricao, impacto=round(valor * derivada, 1))
            for variavel, descricao, valor in contribuicoes
            if abs(valor) >= 0.05
        ]
        fatores.sort(key=lambda fator: abs(fator.impacto), reverse=True)

        return Previsao(
            probabilidade_risco=round(probabilidade, 4),
            nivel_risco=classificar(probabilidade),
            fatores=fatores[:6],
            modelo=self.nome,
        )

    def analisar_municipio(self, municipio: str, uf: str) -> AnaliseMunicipio:
        semente = int(hashlib.sha256(f"{municipio.casefold()}|{uf}".encode()).hexdigest(), 16)

        def numero(indice: int, minimo: float, maximo: float) -> float:
            fracao = ((semente >> (indice * 8)) % 1000) / 999
            return minimo + fracao * (maximo - minimo)

        total_escolas = int(numero(0, 3, 40))
        escolas: list[EscolaResumo] = []
        for i in range(total_escolas):
            risco = round(numero(i + 1, 5, 75), 2)
            escolas.append(
                EscolaResumo(
                    co_escola=35_000_000 + (semente >> i) % 1_000_000,
                    total_alunos_escola=int(numero(i + 2, 8, 60)),
                    media_escola=round(numero(i + 3, 450, 640), 2),
                    percentual_risco_escola=risco,
                    status_alerta="ALTO_RISCO" if risco >= 50 else "MEDIO_RISCO" if risco >= 25 else "BAIXO_RISCO",
                )
            )
        escolas.sort(key=lambda e: e.percentual_risco_escola, reverse=True)

        total_alunos = sum(e.total_alunos_escola for e in escolas)
        media = sum(e.media_escola * e.total_alunos_escola for e in escolas) / total_alunos
        risco = sum(e.percentual_risco_escola * e.total_alunos_escola for e in escolas) / total_alunos

        return AnaliseMunicipio(
            municipio=municipio,
            uf=uf,
            estatisticas_gerais=EstatisticasMunicipio(
                total_alunos_avaliados=total_alunos,
                total_escolas_unicas=len(escolas),
                media_geral=round(media, 2),
                percentual_risco_municipio=round(risco, 2),
            ),
            escolas=escolas,
            modelo=self.nome,
        )


def criar_preditor(usar_mock: bool = True) -> Preditor:
    if usar_mock:
        return PreditorMock()
    raise NotImplementedError(
        "O modelo real ainda não foi integrado. Defina USAR_MOCK=true até a Sprint 3."
    )
