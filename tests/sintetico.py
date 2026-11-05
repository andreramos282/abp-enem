"""Gera um CSV falso no MESMO layout do MICRODADOS_ENEM_2023.csv, para testes.

As notas dependem do perfil (renda, escolaridade dos pais, internet, rede...)
com ruído, para o pipeline ter algo a aprender. NÃO são dados reais.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ml import colunas_2023 as c

MUNICIPIOS = [("Jacareí", "SP"), ("São José dos Campos", "SP"), ("Recife", "PE"), ("Manaus", "AM"), ("Curitiba", "PR")]


def gerar(n: int = 6000, semente: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(semente)
    renda = rng.choice(list("ABCDEFGHIJKLMNOPQ"), n, p=np.array([3, 22, 18, 12, 9, 7, 8, 5, 4, 3, 2, 2, 1.5, 1.2, 1, 0.8, 0.5]) / 100)
    esc_mae = rng.choice(list("ABCDEFGH"), n, p=[0.02, 0.12, 0.15, 0.15, 0.32, 0.14, 0.07, 0.03])
    esc_pai = rng.choice(list("ABCDEFGH"), n, p=[0.03, 0.16, 0.15, 0.14, 0.28, 0.1, 0.05, 0.09])
    rede = rng.choice([1, 2, 3, 4, np.nan], n, p=[0.03, 0.62, 0.03, 0.17, 0.15])
    municipio = rng.integers(0, len(MUNICIPIOS), n)
    df = pd.DataFrame({
        "NU_INSCRICAO": np.arange(n),
        "Q001": esc_pai, "Q002": esc_mae,
        "Q003": rng.choice(list("ABCDEF"), n), "Q004": rng.choice(list("ABCDEF"), n),
        "Q005": rng.integers(1, 9, n), "Q006": renda,
        "Q024": rng.choice(list("ABCDE"), n, p=[0.4, 0.4, 0.12, 0.05, 0.03]),
        "Q025": rng.choice(list("AB"), n, p=[0.12, 0.88]),
        "TP_ESCOLA": np.where(rede == 4, 3, np.where(np.isnan(rede), 1, 2)),
        "TP_DEPENDENCIA_ADM_ESC": rede,
        "TP_LOCALIZACAO_ESC": np.where(np.isnan(rede), np.nan, rng.choice([1, 2], n, p=[0.93, 0.07])),
        "SG_UF_ESC": [MUNICIPIOS[i][1] for i in municipio],
        "NO_MUNICIPIO_ESC": [MUNICIPIOS[i][0] for i in municipio],
        "CO_ESCOLA": 35_000_000 + municipio * 100 + rng.integers(0, 12, n),
        "TP_FAIXA_ETARIA": rng.choice([1, 2, 3, 4, 5, 8], n, p=[0.1, 0.55, 0.22, 0.07, 0.04, 0.02]),
        "TP_COR_RACA": rng.choice([0, 1, 2, 3, 4, 5], n, p=[0.02, 0.4, 0.12, 0.43, 0.02, 0.01]),
        "TP_SEXO": rng.choice(["F", "M"], n, p=[0.6, 0.4]),
        "TP_ST_CONCLUSAO": rng.choice([1, 2, 3], n, p=[0.3, 0.6, 0.1]),
    })
    for col in c.BENS:
        df[col] = rng.choice(list("ABC"), n, p=[0.5, 0.35, 0.15])
    for col in c.PRESENCAS:
        df[col] = rng.choice([0, 1], n, p=[0.08, 0.92])
    df["TP_STATUS_REDACAO"] = rng.choice([1, 4], n, p=[0.95, 0.05])

    ordem = {letra: i for i, letra in enumerate("ABCDEFGH")}
    base = (
        430
        + 9 * pd.Series(renda).map({l: i for i, l in enumerate("ABCDEFGHIJKLMNOPQ")}).to_numpy()
        + 9 * pd.Series(esc_mae).map(ordem).clip(upper=6).to_numpy()
        + 25 * (df["Q025"] == "B")
        + 20 * (df["Q024"] != "A")
        + np.where(rede == 4, 60, np.where(rede == 1, 70, 0))
    )
    for col in c.NOTAS:
        df[col] = np.round(base + rng.normal(0, 55, n), 1)
    ausente = df["TP_PRESENCA_MT"] == 0
    df.loc[ausente, c.NOTAS] = np.nan
    return df


def salvar(caminho: Path, n: int = 6000) -> Path:
    gerar(n).to_csv(caminho, sep=";", index=False, encoding="latin-1")
    return caminho


if __name__ == "__main__":
    import sys
    print(salvar(Path(sys.argv[1] if len(sys.argv) > 1 else "data/MICRODADOS_ENEM_2023_SINTETICO.csv")))
