"""Risco previsto de cada aluno da amostra, calculado uma vez e salvo para a API.

Uso:
    python -m ml.risco_municipios
    (também roda sozinho no fim de python -m ml.treinar)

O painel do município precisa do risco de todos os ~400 mil alunos da amostra. Calcular isso
dentro da API leva mais de um minuto e estoura a memória no plano gratuito do Render. Aqui o
cálculo é feito no computador de quem treinou, e a API só lê o resultado
(data/risco_municipios.parquet, ~3 MB). O arquivo guarda a versão do modelo: se o modelo mudar
e o arquivo não for refeito, a API percebe e calcula do jeito antigo.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from . import colunas_2023 as c
from .features import renomear_microdados
from .preparar_dados import carregar

BLOCO = 10_000  # alunos por vez (limita o pico de memória)
COLUNAS = ["_municipio", "_uf", "rede_escola", "co_escola", "_risco", "_media"]


def calcular(pipeline, entradas: list[str], caminho_amostra: Path) -> pd.DataFrame:
    """Uma linha por aluno com escola informada: município, UF, rede, escola, risco previsto e média."""
    inep = {**c.VARIAVEIS, **c.VARIAVEIS_CONTEXTO}
    colunas = [inep.get(col, col) for col in [*entradas, "municipio_escola", "co_escola"]]
    df = renomear_microdados(carregar(caminho_amostra, colunas=[*colunas, "media_notas"], economizar_memoria=True))
    df = df.dropna(subset=["municipio_escola"]).reset_index(drop=True)

    riscos = [
        pipeline.predict_proba(df.iloc[i : i + BLOCO].reindex(columns=entradas))[:, 1] for i in range(0, len(df), BLOCO)
    ]
    saida = pd.DataFrame(
        {
            "_municipio": df["municipio_escola"].astype("string").str.strip().str.casefold().astype("category"),
            "_uf": df["uf_escola"].astype("string").str.strip().str.upper().astype("category"),
            "rede_escola": pd.to_numeric(df["rede_escola"], errors="coerce").fillna(0).astype("int8"),
            "_risco": np.concatenate(riscos).astype("float32") if riscos else np.array([], dtype="float32"),
            "_media": df["media_notas"].astype("float32"),
        }
    )
    if "co_escola" in df.columns:
        saida["co_escola"] = pd.to_numeric(df["co_escola"], errors="coerce").astype("Int64")
    return saida


def salvar(tabela: pd.DataFrame, caminho: Path, versao_modelo: str) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    arrow = pa.Table.from_pandas(tabela, preserve_index=False)
    arrow = arrow.replace_schema_metadata({**(arrow.schema.metadata or {}), b"modelo": versao_modelo.encode()})
    caminho.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(arrow, caminho, compression="zstd")


def ler(caminho: Path, versao_modelo: str) -> pd.DataFrame | None:
    """Lê o arquivo se ele foi feito com este modelo; senão devolve None."""
    import pyarrow.parquet as pq

    if not caminho.is_file():
        return None
    metadados = pq.read_schema(caminho).metadata or {}
    if metadados.get(b"modelo", b"").decode() != versao_modelo:
        return None
    return pq.read_table(caminho).to_pandas()


def gerar(pasta_modelo: Path, caminho_amostra: Path, saida: Path) -> Path:
    metadados = json.loads((pasta_modelo / "metadados.json").read_text(encoding="utf-8"))
    pipeline = joblib.load(pasta_modelo / "pipeline.pkl")
    tabela = calcular(pipeline, metadados["entradas"], caminho_amostra)
    salvar(tabela, saida, metadados["versao"])
    return saida


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--modelo", type=Path, default=Path("models"))
    parser.add_argument("--amostra", type=Path, default=Path("data/amostra_enem_2023.parquet"))
    parser.add_argument("--saida", type=Path, default=Path("data/risco_municipios.parquet"))
    args = parser.parse_args()
    caminho = gerar(args.modelo, args.amostra, args.saida)
    print(f"Risco por aluno salvo em {caminho} ({caminho.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
