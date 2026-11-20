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

import contextlib
import ctypes
import gc
import json
import math
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from ml import colunas_2023 as c
from ml import risco_municipios
from ml.features import GRUPOS_FATORES

from .regras import classificar, renda_per_capita, status_escola
from .schemas import (
    AnaliseMunicipio,
    Comparacao,
    EscolaResumo,
    EstatisticasMunicipio,
    Fator,
    PerfilAluno,
    Previsao,
    ResumoModelo,
    RiscoPorRede,
)
from .traducoes import FATORES, OPCOES, REDE_NAO_INFORMADA, REGIOES, Idioma, formatar_reais

IMPACTO_MINIMO = 0.5  # pontos percentuais
MAX_FATORES = 6  # fatores em que a escola ou a família podem atuar
MAX_CONTEXTO = 3  # fatores de contexto (o aluno não muda): mostrados à parte
GRUPOS_CONTEXTO = {"cor_raca", "sexo", "regiao"}


class PreditorModelo:
    def __init__(self, pasta_modelo: Path, caminho_amostra: Path | None = None, caminho_risco: Path | None = None):
        self.pasta_modelo = pasta_modelo
        self.pipeline = joblib.load(pasta_modelo / "pipeline.pkl")
        self.metadados = json.loads((pasta_modelo / "metadados.json").read_text(encoding="utf-8"))
        self.nome = self.metadados.get("versao", "modelo")
        self.entradas: list[str] = self.metadados["entradas"]
        self.referencia: dict = self.metadados["referencia"]
        equidade = self.metadados.get("equidade") or {}
        self.limiar_geral: float | None = self.metadados.get("limiar_decisao")
        self.limiares_cor: dict[str, float] = equidade.get("limiares_cor_raca", {})
        self.caminho_amostra = caminho_amostra
        self.caminho_risco = caminho_risco
        self._amostra: pd.DataFrame | None = None
        self._por_uf: pd.DataFrame | None = None
        self._brasil: tuple[float, float] | None = None

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
            if (grupo == "bens" and not perfil.bens) or (grupo == "sexo" and perfil.sexo is None):
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
                tipo="contexto" if grupo in GRUPOS_CONTEXTO else "acao",
            )
            for grupo, p_ref in zip(grupos, probabilidades[1:], strict=True)
            if abs(probabilidade - p_ref) * 100 >= IMPACTO_MINIMO
        ]
        fatores.sort(key=lambda f: abs(f.impacto), reverse=True)
        acao = [f for f in fatores if f.tipo == "acao"][:MAX_FATORES]
        contexto = [f for f in fatores if f.tipo == "contexto"][:MAX_CONTEXTO]

        return Previsao(
            probabilidade_risco=round(probabilidade, 4),
            nivel_risco=classificar(probabilidade),
            fatores=acao + contexto,
            acompanhamento_recomendado=self._acompanhamento(probabilidade, perfil),
            modelo=self.nome,
        )

    def resumo(self) -> ResumoModelo:
        m = self.metadados
        teste = m["resultados"][m["modelo"]]["teste"]
        outro = sorted(self.pasta_modelo.glob("teste_temporal_*.json"))
        temporal = json.loads(outro[-1].read_text(encoding="utf-8")) if outro else None
        return ResumoModelo(
            modelo=self.nome,
            simulado=False,
            treinado_em=m.get("treinado_em"),
            ano_dados=m.get("ano_dados"),
            alunos_amostra=m["amostra"]["total"],
            corte_media=m["alvo"]["corte_media"],
            auc_teste=teste["auc"],
            recall_teste=teste["recall"],
            auc_outro_ano=temporal["teste"]["auc"] if temporal else None,
            outro_ano=temporal["ano"] if temporal else None,
            calibracao_erro_medio=(m.get("calibracao") or {}).get("erro_medio"),
            importancia=(m.get("importancia_shap") or {}).get("pontos_percentuais", {}),
        )

    def prever_lote(self, perfis: list[PerfilAluno]) -> list[Previsao]:
        """Só a probabilidade de cada aluno (sem fatores): uma única chamada ao modelo."""
        tabela = pd.DataFrame([self._linha(p) for p in perfis], columns=self.entradas)
        probabilidades = self.pipeline.predict_proba(tabela)[:, 1]
        return [
            Previsao(
                probabilidade_risco=round(float(p), 4),
                nivel_risco=classificar(float(p)),
                fatores=[],
                acompanhamento_recomendado=self._acompanhamento(float(p), perfil),
                modelo=self.nome,
            )
            for p, perfil in zip(probabilidades, perfis, strict=True)
        ]

    def _acompanhamento(self, probabilidade: float, perfil: PerfilAluno) -> bool | None:
        """Compara com o limiar do grupo de cor/raça (equidade) ou, sem ele, com o limiar geral."""
        if self.limiar_geral is None:
            return None
        cor = str(perfil.cor_raca if perfil.cor_raca is not None else 0)
        return probabilidade >= self.limiares_cor.get(cor, self.limiar_geral)

    # ------------------------------------------------------------------ município
    def _carregar_amostra(self) -> pd.DataFrame:
        """Risco previsto de cada aluno da amostra (com escola informada).

        Lê data/risco_municipios.parquet, calculado fora da API (python -m ml.risco_municipios).
        Se o arquivo não existir ou for de outro modelo, calcula aqui: funciona, mas é lento e
        usa muita memória (não cabe no plano gratuito do Render).
        """
        if self._amostra is None:
            df = risco_municipios.ler(self.caminho_risco, self.nome) if self.caminho_risco else None
            if df is None:
                if not self.caminho_amostra or not self.caminho_amostra.is_file():
                    raise LookupError("Amostra do ENEM não encontrada. Gere com: python -m ml.preparar_dados")
                df = risco_municipios.calcular(self.pipeline, self.entradas, self.caminho_amostra)
            self._por_uf = df.groupby("_uf", observed=True)[["_risco", "_media"]].mean()
            self._brasil = (float(df["_risco"].mean()), float(df["_media"].mean()))
            self._amostra = df
            _devolver_memoria()
        return self._amostra

    def analisar_municipio(self, municipio: str, uf: str, idioma: Idioma = "pt") -> AnaliseMunicipio:
        amostra = self._carregar_amostra()
        dados = amostra[(amostra["_municipio"] == municipio.strip().casefold()) & (amostra["_uf"] == uf)].copy()
        if dados.empty:
            raise LookupError("Nenhum aluno da amostra para este município.")
        # Risco previsto = probabilidade média (parcela esperada de alunos no quartil inferior).

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

        comparacao = None
        if self._por_uf is not None and self._brasil is not None and uf in self._por_uf.index:
            estado = self._por_uf.loc[uf]
            comparacao = Comparacao(
                percentual_risco_uf=round(float(estado["_risco"]) * 100, 2),
                percentual_risco_brasil=round(self._brasil[0] * 100, 2),
                media_uf=round(float(estado["_media"]), 2),
                media_brasil=round(self._brasil[1], 2),
            )

        rotulos_rede = OPCOES[idioma]["rede_escola"]
        rede = pd.to_numeric(dados["rede_escola"], errors="coerce").fillna(0).astype(int)
        por_rede = [
            RiscoPorRede(
                rede_escola=int(codigo),
                rotulo=rotulos_rede.get(int(codigo), REDE_NAO_INFORMADA[idioma]),
                total_alunos=int(len(grupo)),
                percentual_risco=round(float(grupo["_risco"].mean()) * 100, 2),
                media=round(float(grupo["_media"].mean()), 2),
            )
            for codigo, grupo in dados.groupby(rede)
        ]
        por_rede.sort(key=lambda r: r.total_alunos, reverse=True)

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
            comparacao=comparacao,
            por_rede=por_rede,
            modelo=self.nome,
        )


def _devolver_memoria() -> None:
    """Devolve ao sistema a memória liberada depois de carregar a amostra (ajuda no plano de 512 MB)."""
    gc.collect()
    with contextlib.suppress(OSError, AttributeError):  # fora do Linux/glibc não há malloc_trim
        ctypes.CDLL("libc.so.6").malloc_trim(0)


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
    if grupo == "cor_raca":
        return frases["cor_raca"].format(valor=opcoes["cor_raca"][perfil.cor_raca or 0].lower())
    if grupo == "sexo" and perfil.sexo:
        return frases["sexo"].format(valor=opcoes["sexo"][perfil.sexo].lower())
    if grupo == "regiao":
        return frases["regiao"].format(valor=REGIOES[idioma][c.REGIAO_POR_UF[perfil.uf_escola]])
    return frases.get(grupo, grupo)
