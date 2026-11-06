"""Preditor com o modelo treinado (models/pipeline.pkl).

Explicação de cada previsão (fatores): para cada grupo de respostas, troca o
valor do aluno pela resposta mais comum no treino (perfil de referência) e mede
quanto a probabilidade muda. Impacto positivo = aquela resposta aumenta o risco
em relação ao perfil típico. Funciona com qualquer modelo, inclusive a MLP.

Análise por município: usa a amostra do ENEM 2023 (data/amostra_enem_2023.parquet).
Como é uma amostra, os totais por município são menores que os reais. O "% de risco"
é a probabilidade média prevista, ou seja, a parcela esperada de alunos no quartil
inferior (a média nacional é 25%). Os microdados de 2023 não trazem o código da
escola, então a lista de escolas fica vazia com esta base.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from ml import colunas_2023 as c
from ml.features import GRUPOS_FATORES, renomear_microdados
from ml.preparar_dados import carregar

from .regras import classificar, renda_per_capita, status_escola
from .schemas import AnaliseMunicipio, EscolaResumo, EstatisticasMunicipio, Fator, PerfilAluno, Previsao
from .traducoes import FATORES, OPCOES, REGIOES, Idioma, formatar_reais

IMPACTO_MINIMO = 0.5  # pontos percentuais
MAX_FATORES = 6


class PreditorModelo:
    def __init__(self, pasta_modelo: Path, caminho_amostra: Path | None = None):
        self.pipeline = joblib.load(pasta_modelo / "pipeline.pkl")
        self.metadados = json.loads((pasta_modelo / "metadados.json").read_text(encoding="utf-8"))
        self.nome = self.metadados.get("versao", "modelo")
        self.entradas: list[str] = self.metadados["entradas"]
        self.referencia: dict = self.metadados["referencia"]
        self.caminho_amostra = caminho_amostra
        self._amostra: pd.DataFrame | None = None

    # ------------------------------------------------------------------ previsão
    def _linha(self, perfil: PerfilAluno) -> dict:
        dados = perfil.model_dump(exclude={"bens"})
        dados.update(perfil.bens)
        return {col: dados.get(col, np.nan) for col in self.entradas}

    def prever(self, perfil: PerfilAluno, idioma: Idioma = "pt") -> Previsao:
        linha = self._linha(perfil)
        variantes = [linha]
        grupos: list[str] = []
        for grupo, colunas in GRUPOS_FATORES.items():
            colunas = [col for col in colunas if col in self.entradas]
            if grupo == "bens" and not perfil.bens:
                continue
            if not colunas or all(_igual(linha[col], self.referencia.get(col)) for col in colunas):
                continue
            variante = dict(linha)
            for col in colunas:
                variante[col] = self.referencia.get(col)
            variantes.append(variante)
            grupos.append(grupo)

        probabilidades = self.pipeline.predict_proba(pd.DataFrame(variantes, columns=self.entradas))[:, 1]
        probabilidade = float(probabilidades[0])

        fatores = [
            Fator(
                variavel=grupo,
                descricao=_descrever(grupo, perfil, idioma),
                impacto=round((probabilidade - p_ref) * 100, 1),
            )
            for grupo, p_ref in zip(grupos, probabilidades[1:], strict=True)
            if abs(probabilidade - p_ref) * 100 >= IMPACTO_MINIMO
        ]
        fatores.sort(key=lambda f: abs(f.impacto), reverse=True)

        return Previsao(
            probabilidade_risco=round(probabilidade, 4),
            nivel_risco=classificar(probabilidade),
            fatores=fatores[:MAX_FATORES],
            modelo=self.nome,
        )

    # ------------------------------------------------------------------ município
    def _carregar_amostra(self) -> pd.DataFrame:
        """Carrega só as colunas necessárias e guarda textos como categorias.

        Lida inteira, a amostra ocupa ~600 MB de memória; assim fica em torno de 30 MB,
        o que cabe em servidores pequenos (ex.: plano gratuito do Render, 512 MB).
        """
        if self._amostra is None:
            if not self.caminho_amostra or not self.caminho_amostra.is_file():
                raise LookupError("Amostra do ENEM não encontrada. Gere com: python -m ml.preparar_dados")
            inep = {**c.VARIAVEIS, **c.VARIAVEIS_CONTEXTO}
            colunas = [inep.get(col, col) for col in [*self.entradas, "municipio_escola", "co_escola"]]
            df = renomear_microdados(
                carregar(self.caminho_amostra, colunas=[*colunas, "media_notas"], economizar_memoria=True)
            )
            df = df.dropna(subset=["municipio_escola"])
            df["_municipio"] = df["municipio_escola"].astype("string").str.strip().str.casefold().astype("category")
            df["_uf"] = df["uf_escola"].astype("string").str.strip().str.upper().astype("category")
            df = df.drop(columns="municipio_escola")
            self._amostra = df
        return self._amostra

    def analisar_municipio(self, municipio: str, uf: str) -> AnaliseMunicipio:
        amostra = self._carregar_amostra()
        dados = amostra[(amostra["_municipio"] == municipio.strip().casefold()) & (amostra["_uf"] == uf)].copy()
        if dados.empty:
            raise LookupError("Nenhum aluno da amostra para este município.")

        prob = self.pipeline.predict_proba(dados.reindex(columns=self.entradas))[:, 1]
        # Risco previsto = probabilidade média (parcela esperada de alunos no quartil inferior).
        dados["_risco"] = prob
        dados["_media"] = dados["media_notas"].astype(float)

        escolas: list[EscolaResumo] = []
        if "co_escola" in dados.columns:
            por_escola = (
                dados.dropna(subset=["co_escola"])
                .groupby("co_escola")
                .agg(total=("_risco", "size"), media=("_media", "mean"), risco=("_risco", "mean"))
                .reset_index()
            )
            for linha in por_escola.itertuples(index=False):
                percentual = float(linha.risco) * 100
                escolas.append(
                    EscolaResumo(
                        co_escola=int(linha.co_escola),
                        total_alunos_escola=int(linha.total),
                        media_escola=round(float(linha.media), 2),
                        percentual_risco_escola=round(percentual, 2),
                        status_alerta=status_escola(percentual),
                    )
                )
            escolas.sort(key=lambda e: (e.percentual_risco_escola, e.total_alunos_escola), reverse=True)

        return AnaliseMunicipio(
            municipio=municipio,
            uf=uf,
            estatisticas_gerais=EstatisticasMunicipio(
                total_alunos_avaliados=len(dados),
                total_escolas_unicas=len(escolas),
                media_geral=round(float(dados["_media"].mean()), 2),
                percentual_risco_municipio=round(float(dados["_risco"].mean()) * 100, 2),
            ),
            escolas=escolas,
            modelo=self.nome,
        )


def _igual(a, b) -> bool:
    if a is None or b is None:
        return a is b
    if isinstance(a, float) and math.isnan(a):
        return isinstance(b, float) and math.isnan(b)
    try:
        return float(a) == float(b)
    except (TypeError, ValueError):
        return str(a).strip().upper() == str(b).strip().upper()


def _descrever(grupo: str, perfil: PerfilAluno, idioma: Idioma) -> str:
    frases = FATORES[idioma]
    opcoes = OPCOES[idioma]
    if grupo == "renda_per_capita":
        return frases["renda_per_capita"].format(valor=formatar_reais(renda_per_capita(perfil), idioma))
    if grupo in {"escolaridade_mae", "escolaridade_pai"}:
        return frases[grupo].format(valor=opcoes["escolaridade"][getattr(perfil, grupo)].lower())
    if grupo in {"ocupacao_mae", "ocupacao_pai"}:
        return frases[grupo].format(valor=opcoes["ocupacao"][getattr(perfil, grupo)])
    if grupo == "computador":
        return frases["sem_computador" if perfil.computador == "A" else "com_computador"]
    if grupo == "internet":
        return frases["sem_internet" if perfil.internet == "A" else "com_internet"]
    if grupo in {"rede_escola", "localizacao_escola", "faixa_etaria"}:
        return frases[grupo].format(valor=opcoes[grupo][getattr(perfil, grupo)].lower())
    if grupo == "regiao":
        return frases["regiao"].format(valor=REGIOES[idioma][c.REGIAO_POR_UF[perfil.uf_escola]])
    return frases.get(grupo, grupo)
