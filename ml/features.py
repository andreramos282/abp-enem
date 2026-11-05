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
    "bens": c.BENS,
}


def _codigo(serie: pd.Series) -> pd.Series:
    return serie.astype("string").str.strip().str.upper()


def transformar(df: pd.DataFrame) -> pd.DataFrame:
    """Converte as respostas do questionário em variáveis para o modelo."""
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
        itens = pd.concat([_codigo(df[col]).map(_ITEM_BEM).astype(float) for col in bens], axis=1)
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

    return saida[NUMERICAS + CATEGORICAS]


def construir_preprocessador() -> ColumnTransformer:
    numericas = Pipeline(
        [
            ("imputar", SimpleImputer(strategy="median", add_indicator=True)),
            ("padronizar", StandardScaler()),
        ]
    )
    categoricas = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    return ColumnTransformer(
        [("num", numericas, NUMERICAS), ("cat", categoricas, CATEGORICAS)],
        verbose_feature_names_out=False,
    )


def construir_pipeline(modelo) -> Pipeline:
    """Pipeline completo: variáveis do projeto -> pré-processamento -> classificador."""
    return Pipeline(
        [
            ("variaveis", FunctionTransformer(transformar)),
            ("preprocessamento", construir_preprocessador()),
            ("modelo", modelo),
        ]
    )


def renomear_microdados(df: pd.DataFrame) -> pd.DataFrame:
    """Troca os nomes do INEP (Q001, TP_ESCOLA...) pelos nomes do projeto."""
    mapa = {inep: nome for nome, inep in c.VARIAVEIS.items()}
    mapa.update({inep: nome for nome, inep in c.VARIAVEIS_ANALISE_VIES.items()})
    mapa.update({inep: nome for nome, inep in c.VARIAVEIS_CONTEXTO.items()})
    return df.rename(columns=mapa)
