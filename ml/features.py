"""Engenharia de variáveis usada IGUAL no treino e na API.

Entrada: DataFrame com os nomes do projeto (escolaridade_mae, renda_familiar...)
e, opcionalmente, os itens de bens Q007 a Q023.
Saída: DataFrame numérico/categórico pronto para o pré-processador do scikit-learn.

Como esta função vai dentro do Pipeline salvo em models/pipeline.pkl, a API
aplica exatamente o mesmo tratamento usado no treino.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

from . import colunas_2023 as c

# Colunas de entrada esperadas (nomes do projeto).
ENTRADAS = list(c.VARIAVEIS)

# Ordem das respostas: A = menor ... (o "Não sei" vira ausente e ganha um indicador).
_ESCOLARIDADE = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4, "F": 5, "G": 6}
_OCUPACAO = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5}
_COMPUTADOR = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4}
_INTERNET = {"A": 0, "B": 1}
_ITEM_BEM = {letra: i for i, letra in enumerate("ABCDE")}

NUMERICAS = [
    "escolaridade_pai",
    "escolaridade_mae",
    "ocupacao_pai",
    "ocupacao_mae",
    "pessoas_residencia",
    "renda_familiar",
    "renda_per_capita_log",
    "computador",
    "internet",
    "indice_bens",
    "faixa_etaria",
]
CATEGORICAS = ["rede_escola", "localizacao_escola", "tipo_escola", "regiao"]
# Cor/raça e sexo: podem ser ligadas ou desligadas (sensiveis=False) para comparar o efeito delas.
CATEGORICAS_SENSIVEIS = list(c.SENSIVEIS)

# Grupos de entradas usados para explicar a previsão (ver api/modelo.py).
GRUPOS_FATORES: dict[str, list[str]] = {
    "renda_per_capita": ["renda_familiar", "pessoas_residencia"],
    "escolaridade_mae": ["escolaridade_mae"],
    "escolaridade_pai": ["escolaridade_pai"],
    "ocupacao_mae": ["ocupacao_mae"],
    "ocupacao_pai": ["ocupacao_pai"],
    "computador": ["computador"],
    "internet": ["internet"],
    "rede_escola": ["rede_escola", "tipo_escola"],
    "localizacao_escola": ["localizacao_escola"],
    "regiao": ["uf_escola"],
    "faixa_etaria": ["faixa_etaria"],
    "cor_raca": ["cor_raca"],
    "sexo": ["sexo"],
    "bens": c.BENS,
}


def _codigo(serie: pd.Series) -> pd.Series:
    return serie.astype("string").str.strip().str.upper()


def colunas_saida(sensiveis: bool = True) -> tuple[list[str], list[str]]:
    """Colunas numéricas e categóricas geradas por transformar()."""
    return NUMERICAS, CATEGORICAS + (CATEGORICAS_SENSIVEIS if sensiveis else [])


def transformar(df: pd.DataFrame, sensiveis: bool = True) -> pd.DataFrame:
    """Converte as respostas do questionário em variáveis para o modelo.

    sensiveis=False deixa cor/raça e sexo de fora (usado na comparação do treino).
    """
    saida = pd.DataFrame(index=df.index)

    saida["escolaridade_pai"] = _codigo(df["escolaridade_pai"]).map(_ESCOLARIDADE).astype(float)
    saida["escolaridade_mae"] = _codigo(df["escolaridade_mae"]).map(_ESCOLARIDADE).astype(float)
    saida["ocupacao_pai"] = _codigo(df["ocupacao_pai"]).map(_OCUPACAO).astype(float)
    saida["ocupacao_mae"] = _codigo(df["ocupacao_mae"]).map(_OCUPACAO).astype(float)

    pessoas = pd.to_numeric(df["pessoas_residencia"], errors="coerce").clip(lower=1)
    renda = _codigo(df["renda_familiar"]).map(c.RENDA_VALOR_MEDIO).astype(float)
    saida["pessoas_residencia"] = pessoas
    saida["renda_familiar"] = renda
    saida["renda_per_capita_log"] = np.log1p(renda / pessoas)

    saida["computador"] = _codigo(df["computador"]).map(_COMPUTADOR).astype(float)
    saida["internet"] = _codigo(df["internet"]).map(_INTERNET).astype(float)

    bens = [col for col in c.BENS if col in df.columns]
    if bens:
        # Cada item vai para a escala 0–1 (A = 0, última resposta = 1) antes da média.
        itens = pd.concat(
            [_codigo(df[col]).map(_ITEM_BEM).astype(float) / _ITEM_BEM[c.ULTIMA_RESPOSTA_BENS[col]] for col in bens],
            axis=1,
        )
        saida["indice_bens"] = itens.mean(axis=1)
    else:
        saida["indice_bens"] = np.nan

    saida["faixa_etaria"] = pd.to_numeric(df["faixa_etaria"], errors="coerce")

    # Categóricas: ausente vira "0" (escola não informada).
    for coluna in ["rede_escola", "localizacao_escola", "tipo_escola"]:
        valores = pd.to_numeric(df[coluna], errors="coerce").fillna(0).astype(int)
        saida[coluna] = valores.astype(str)
    uf = _codigo(df["uf_escola"])
    saida["regiao"] = uf.map(c.REGIAO_POR_UF).fillna("Nao informada").astype(str)

    if sensiveis:
        # Ausente vira "0" (não declarado) em cor/raça e "NI" (não informado) em sexo.
        cor = df["cor_raca"] if "cor_raca" in df.columns else pd.Series(np.nan, index=df.index)
        sexo = df["sexo"] if "sexo" in df.columns else pd.Series(np.nan, index=df.index)
        saida["cor_raca"] = pd.to_numeric(cor, errors="coerce").fillna(0).astype(int).astype(str)
        saida["sexo"] = _codigo(sexo).fillna("NI").astype(str)

    numericas, categoricas = colunas_saida(sensiveis)
    return saida[numericas + categoricas]


def construir_preprocessador(sensiveis: bool = True) -> ColumnTransformer:
    numericas_cols, categoricas_cols = colunas_saida(sensiveis)
    numericas = Pipeline(
        [
            ("imputar", SimpleImputer(strategy="median", add_indicator=True)),
            ("padronizar", StandardScaler()),
        ]
    )
    categoricas = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    return ColumnTransformer(
        [("num", numericas, numericas_cols), ("cat", categoricas, categoricas_cols)],
        verbose_feature_names_out=False,
    )


def construir_pipeline(modelo, sensiveis: bool = True) -> Pipeline:
    """Pipeline completo: variáveis do projeto -> pré-processamento -> classificador."""
    return Pipeline(
        [
            ("variaveis", FunctionTransformer(transformar, kw_args={"sensiveis": sensiveis})),
            ("preprocessamento", construir_preprocessador(sensiveis)),
            ("modelo", modelo),
        ]
    )


def renomear_microdados(df: pd.DataFrame) -> pd.DataFrame:
    """Troca os nomes do INEP (Q001, TP_ESCOLA...) pelos nomes do projeto."""
    mapa = {inep: nome for nome, inep in c.VARIAVEIS.items()}
    mapa.update({inep: nome for nome, inep in c.VARIAVEIS_CONTEXTO.items()})
    return df.rename(columns=mapa)
