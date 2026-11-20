"""Preditor simulado (mock).

Regra simples e determinística que devolve respostas no formato final, para o
front-end funcionar antes do modelo treinado. Os valores NÃO vêm de modelo
treinado e não devem ser usados como resultado do projeto.
"""

from __future__ import annotations

import hashlib
import math

from .regras import classificar, renda_per_capita, status_escola
from .schemas import (
    AnaliseMunicipio,
    Comparacao,
    EscolaResumo,
    EstatisticasMunicipio,
    Fator,
    PerfilAluno,
    Previsao,
    RiscoPorRede,
)
from .traducoes import FATORES, OPCOES, Idioma, formatar_reais


class PreditorMock:
    """Respostas simuladas e determinísticas (o mesmo perfil sempre gera o mesmo resultado)."""

    nome = "mock"

    _ESCOLARIDADE_PESO = {"A": 0.9, "B": 0.7, "C": 0.5, "D": 0.3, "E": 0.0, "F": -0.5, "G": -0.7, "H": 0.3}

    def prever(self, perfil: PerfilAluno, idioma: Idioma = "pt") -> Previsao:
        frases = FATORES[idioma]
        opcoes = OPCOES[idioma]
        rpc = renda_per_capita(perfil)
        contribuicoes: list[tuple[str, str, float]] = [
            (
                "renda_per_capita",
                frases["renda_per_capita"].format(valor=formatar_reais(rpc, idioma)),
                0.8 * (3.2 - math.log10(rpc + 50)),
            ),
            (
                "escolaridade_mae",
                frases["escolaridade_mae"].format(valor=opcoes["escolaridade"][perfil.escolaridade_mae].lower()),
                self._ESCOLARIDADE_PESO[perfil.escolaridade_mae],
            ),
            (
                "escolaridade_pai",
                frases["escolaridade_pai"].format(valor=opcoes["escolaridade"][perfil.escolaridade_pai].lower()),
                0.6 * self._ESCOLARIDADE_PESO[perfil.escolaridade_pai],
            ),
            (
                "computador",
                frases["sem_computador" if perfil.computador == "A" else "com_computador"],
                0.45 if perfil.computador == "A" else -0.25,
            ),
            (
                "internet",
                frases["sem_internet" if perfil.internet == "A" else "com_internet"],
                0.4 if perfil.internet == "A" else -0.15,
            ),
            (
                "rede_escola",
                frases["rede_escola"].format(valor=opcoes["rede_escola"][perfil.rede_escola].lower()),
                {1: -0.6, 2: 0.35, 3: 0.4, 4: -0.7}[perfil.rede_escola],
            ),
            (
                "localizacao_escola",
                frases["localizacao_escola"].format(
                    valor=opcoes["localizacao_escola"][perfil.localizacao_escola].lower()
                ),
                0.3 if perfil.localizacao_escola == 2 else 0.0,
            ),
            (
                "faixa_etaria",
                frases["faixa_etaria"].format(valor=opcoes["faixa_etaria"][perfil.faixa_etaria].lower()),
                0.25 * max(0, perfil.faixa_etaria - 3),
            ),
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

    def prever_lote(self, perfis: list[PerfilAluno]) -> list[Previsao]:
        return [self.prever(perfil) for perfil in perfis]

    def analisar_municipio(self, municipio: str, uf: str, idioma: Idioma = "pt") -> AnaliseMunicipio:
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
                    status_alerta=status_escola(risco),
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
            comparacao=Comparacao(
                percentual_risco_uf=round(numero(20, 15, 35), 2),
                percentual_risco_brasil=25.0,
                media_uf=round(numero(21, 500, 560), 2),
                media_brasil=531.0,
            ),
            por_rede=[
                RiscoPorRede(
                    rede_escola=codigo,
                    rotulo=OPCOES[idioma]["rede_escola"][codigo],
                    total_alunos=int(total_alunos * fracao),
                    percentual_risco=round(numero(22 + codigo, minimo, maximo), 2),
                    media=round(numero(26 + codigo, 470, 620), 2),
                )
                for codigo, fracao, minimo, maximo in [(2, 0.7, 25, 45), (4, 0.2, 3, 12), (1, 0.1, 5, 15)]
            ],
            modelo=self.nome,
        )
