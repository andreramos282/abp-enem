"""Gera a amostra do ENEM 2023 usada por todo o grupo.

Uso:
    python -m ml.preparar_dados data/MICRODADOS_ENEM_2023.csv
    python -m ml.preparar_dados data/MICRODADOS_ENEM_2023.csv --tamanho 400000 --saida data/amostra_enem_2023.parquet

O arquivo original tem milhões de linhas, então é lido em blocos, só com as
colunas necessárias. Ficam apenas concluintes presentes nas 4 provas e com
redação válida. A amostra é estratificada por região e tipo de escola.

A amostra mantém os nomes de colunas do INEP e guarda a MÉDIA das notas, não o alvo: o corte do quartil é calculado
no treino (ml/treinar.py), só com os dados de treino.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from . import colunas_2023 as c

COLUNAS_FILTRO = [c.SITUACAO_CONCLUSAO, *c.PRESENCAS, c.STATUS_REDACAO]


def colunas_para_ler(cabecalho: list[str]) -> list[str]:
    desejadas = [
        *c.VARIAVEIS.values(),
        *c.BENS,
        *c.VARIAVEIS_ANALISE_VIES.values(),
        *c.VARIAVEIS_CONTEXTO.values(),
        *c.NOTAS,
        *COLUNAS_FILTRO,
    ]
    obrigatorias = [*c.VARIAVEIS.values(), *c.NOTAS, *COLUNAS_FILTRO]
    faltando = [col for col in obrigatorias if col not in cabecalho]
    if faltando:
        raise SystemExit(
            f"Colunas obrigatórias ausentes no arquivo: {faltando}. "
            "Confira se é o arquivo MICRODADOS_ENEM_2023.csv e o mapeamento em ml/colunas_2023.py."
        )
    return [col for col in dict.fromkeys(desejadas) if col in cabecalho]


def filtrar_bloco(bloco: pd.DataFrame) -> pd.DataFrame:
    filtro = bloco[c.SITUACAO_CONCLUSAO] == c.CONCLUINTE
    for presenca in c.PRESENCAS:
        filtro &= bloco[presenca] == c.PRESENTE
    filtro &= bloco[c.STATUS_REDACAO] == c.REDACAO_VALIDA
    filtro &= bloco[c.NOTAS].notna().all(axis=1)
    selecionado = bloco.loc[filtro].copy()
    selecionado["media_notas"] = selecionado[c.NOTAS].mean(axis=1).astype("float32")
    return selecionado.drop(columns=COLUNAS_FILTRO)


def ler_populacao(caminho: Path, tamanho_bloco: int = 250_000, encoding: str = "latin-1") -> pd.DataFrame:
    cabecalho = pd.read_csv(caminho, sep=";", encoding=encoding, nrows=0).columns.tolist()
    usar = colunas_para_ler(cabecalho)
    texto = {
        col: "string" for col in usar if col.startswith("Q") or col in {"SG_UF_ESC", "TP_SEXO", "NO_MUNICIPIO_ESC"}
    }
    blocos = []
    total_lido = 0
    for bloco in pd.read_csv(caminho, sep=";", encoding=encoding, usecols=usar, dtype=texto, chunksize=tamanho_bloco):
        total_lido += len(bloco)
        blocos.append(filtrar_bloco(bloco))
        print(f"  {total_lido:>10,} linhas lidas · {sum(len(b) for b in blocos):>9,} na população".replace(",", "."))
    return pd.concat(blocos, ignore_index=True)


def amostrar(populacao: pd.DataFrame, tamanho: int, semente: int = c.RANDOM_STATE) -> pd.DataFrame:
    """Amostra estratificada proporcional por região × tipo de escola."""
    if len(populacao) <= tamanho:
        return populacao.sample(frac=1, random_state=semente).reset_index(drop=True)
    regiao = populacao[c.VARIAVEIS["uf_escola"]].map(c.REGIAO_POR_UF).fillna("Nao informada")
    estrato = regiao + "|" + populacao[c.VARIAVEIS["tipo_escola"]].astype(str)
    fracao = tamanho / len(populacao)
    rng = np.random.default_rng(semente)
    partes = []
    for _, grupo in populacao.groupby(estrato, sort=True):
        n = int(round(len(grupo) * fracao))
        if n:
            partes.append(grupo.iloc[rng.choice(len(grupo), size=n, replace=False)])
    return pd.concat(partes).sample(frac=1, random_state=semente).reset_index(drop=True)


def salvar(df: pd.DataFrame, caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    if caminho.suffix == ".parquet":
        df.to_parquet(caminho, index=False)
    else:
        df.to_csv(caminho, index=False)


def carregar(caminho: Path) -> pd.DataFrame:
    if caminho.suffix == ".parquet":
        return pd.read_parquet(caminho)
    return pd.read_csv(
        caminho, dtype={col: "string" for col in [*c.BENS, "Q001", "Q002", "Q003", "Q004", "Q006", "Q024", "Q025"]}
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("entrada", type=Path, help="Caminho do MICRODADOS_ENEM_2023.csv")
    parser.add_argument("--saida", type=Path, default=Path("data/amostra_enem_2023.parquet"))
    parser.add_argument("--tamanho", type=int, default=400_000)
    parser.add_argument("--encoding", default="latin-1")
    args = parser.parse_args()

    print(f"Lendo {args.entrada} ...")
    populacao = ler_populacao(args.entrada, encoding=args.encoding)
    amostra = amostrar(populacao, args.tamanho)
    salvar(amostra, args.saida)

    print(f"\nPopulação (concluintes válidos): {len(populacao):,}".replace(",", "."))
    print(f"Amostra salva em {args.saida}: {len(amostra):,} linhas".replace(",", "."))
    print(f"Quartil inferior da média (referência, na amostra): {amostra['media_notas'].quantile(c.QUANTIL_RISCO):.1f}")


if __name__ == "__main__":
    main()
