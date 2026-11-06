"""Análise exploratória (EDA) da amostra do ENEM 2023.

Uso:
    python -m ml.eda
    python -m ml.eda --amostra data/amostra_enem_2023.parquet --saida docs/eda

Gera gráficos (PNG) e um resumo em Markdown com a taxa de alunos no quartil
inferior (alvo do modelo) para cada característica do perfil.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from . import colunas_2023 as c  # noqa: E402
from .features import renomear_microdados  # noqa: E402
from .preparar_dados import carregar  # noqa: E402

COR = "#4f46e5"
COR_SUAVE = "#c7d2fe"
TEXTO = "#334155"
GRADE = "#e2e8f0"

FAIXAS_RENDA = {
    "A": "Sem renda",
    "B": "Até 1 SM",
    "C": "1 a 2 SM",
    "D": "1 a 2 SM",
    "E": "2 a 3 SM",
    "F": "2 a 3 SM",
    "G": "3 a 5 SM",
    "H": "3 a 5 SM",
    "I": "5 a 10 SM",
    "J": "5 a 10 SM",
    "K": "5 a 10 SM",
    "L": "5 a 10 SM",
    "M": "5 a 10 SM",
    "N": "Mais de 10 SM",
    "O": "Mais de 10 SM",
    "P": "Mais de 10 SM",
    "Q": "Mais de 10 SM",
}
ESCOLARIDADE_CURTA = {
    "A": "Nunca estudou",
    "B": "Fund. I incompleto",
    "C": "Fund. I completo",
    "D": "Fund. II completo",
    "E": "Médio completo",
    "F": "Superior completo",
    "G": "Pós-graduação",
    "H": "Não sabe",
}
REDE = {1: "Federal", 2: "Estadual", 3: "Municipal", 4: "Privada"}


def taxa_por(df: pd.DataFrame, coluna: str, ordem: list[str]) -> pd.DataFrame:
    tabela = df.groupby(coluna, observed=True).agg(alunos=("risco", "size"), taxa_risco=("risco", "mean"))
    tabela["media_notas"] = df.groupby(coluna, observed=True)["media_notas"].mean()
    return tabela.reindex([o for o in ordem if o in tabela.index])


def grafico_barras(tabela: pd.DataFrame, titulo: str, taxa_geral: float, caminho: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 0.5 * len(tabela) + 1.6), dpi=150)
    valores = tabela["taxa_risco"] * 100
    ax.barh(tabela.index.astype(str), valores, color=COR, height=0.6, zorder=2)
    ax.axvline(taxa_geral * 100, color=TEXTO, linewidth=1, linestyle="--", zorder=3)
    ax.annotate(
        f"média geral: {taxa_geral:.0%}",
        xy=(taxa_geral * 100, 0),
        xycoords=("data", "axes fraction"),
        xytext=(4, 4),
        textcoords="offset points",
        fontsize=8,
        color=TEXTO,
        bbox={"facecolor": "white", "edgecolor": "none", "pad": 1},
        zorder=4,
    )
    for i, (v, n) in enumerate(zip(valores, tabela["alunos"], strict=True)):
        ax.text(
            v + 0.8,
            i,
            f"{v:.0f}%  (n={n:,})".replace(",", "."),
            va="center",
            fontsize=8,
            color=TEXTO,
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 1},
            zorder=4,
        )
    ax.invert_yaxis()
    ax.set_xlim(0, max(100, valores.max() + 15))
    ax.set_xlabel("% de alunos no quartil inferior de desempenho", color=TEXTO, fontsize=9)
    ax.set_title(titulo, loc="left", fontsize=11, color="#0f172a", fontweight="bold")
    ax.grid(axis="x", color=GRADE, linewidth=0.8, zorder=0)
    ax.tick_params(colors=TEXTO, labelsize=9, length=0)
    for lado in ["top", "right", "left"]:
        ax.spines[lado].set_visible(False)
    ax.spines["bottom"].set_color(GRADE)
    fig.tight_layout()
    fig.savefig(caminho)
    plt.close(fig)


def grafico_distribuicao(df: pd.DataFrame, corte: float, caminho: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 3.6), dpi=150)
    contagem, bordas = np.histogram(df["media_notas"], bins=80)
    centros = (bordas[:-1] + bordas[1:]) / 2
    cores = [COR if centro < corte else COR_SUAVE for centro in centros]
    ax.bar(centros, contagem, width=np.diff(bordas) * 0.9, color=cores, zorder=2)
    ax.axvline(corte, color=TEXTO, linestyle="--", linewidth=1)
    ax.text(
        corte + 5,
        ax.get_ylim()[1] * 0.9,
        f"corte do quartil inferior: {corte:.0f}",
        fontsize=8,
        color=TEXTO,
        bbox={"facecolor": "white", "edgecolor": "none", "pad": 1},
    )
    ax.set_title("Distribuição da média das 5 notas (concluintes)", loc="left", fontsize=11, fontweight="bold")
    ax.set_xlabel("Média das notas", color=TEXTO, fontsize=9)
    ax.set_ylabel("Alunos", color=TEXTO, fontsize=9)
    ax.grid(axis="y", color=GRADE, linewidth=0.8, zorder=0)
    ax.tick_params(colors=TEXTO, labelsize=8, length=0)
    for lado in ["top", "right"]:
        ax.spines[lado].set_visible(False)
    fig.tight_layout()
    fig.savefig(caminho)
    plt.close(fig)


def tabela_md(tabela: pd.DataFrame, nome: str) -> list[str]:
    linhas = [f"| {nome} | Alunos | % no quartil inferior | Média das notas |", "| --- | --- | --- | --- |"]
    for indice, r in tabela.iterrows():
        alunos = f"{int(r['alunos']):,}".replace(",", ".")
        linhas.append(f"| {indice} | {alunos} | {r['taxa_risco']:.1%} | {r['media_notas']:.1f} |")
    return linhas


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--amostra", type=Path, default=Path("data/amostra_enem_2023.parquet"))
    parser.add_argument("--saida", type=Path, default=Path("docs/eda"))
    args = parser.parse_args()
    args.saida.mkdir(parents=True, exist_ok=True)

    df = renomear_microdados(carregar(args.amostra))
    corte = float(df["media_notas"].quantile(c.QUANTIL_RISCO))
    df["risco"] = (df["media_notas"] < corte).astype(int)
    taxa_geral = float(df["risco"].mean())

    df["Renda familiar"] = df["renda_familiar"].astype("string").map(FAIXAS_RENDA)
    df["Escolaridade da mãe"] = df["escolaridade_mae"].astype("string").map(ESCOLARIDADE_CURTA)
    df["Rede da escola"] = pd.to_numeric(df["rede_escola"], errors="coerce").map(REDE).fillna("Não informada")
    df["Região"] = df["uf_escola"].astype("string").map(c.REGIAO_POR_UF).fillna("Não informada")
    df["Internet em casa"] = df["internet"].astype("string").map({"A": "Não", "B": "Sim"})
    df["Computador em casa"] = (
        df["computador"]
        .astype("string")
        .map({"A": "Nenhum", "B": "Um", "C": "Dois ou mais", "D": "Dois ou mais", "E": "Dois ou mais"})
    )
    df["Localização da escola"] = pd.to_numeric(df["localizacao_escola"], errors="coerce").map(
        {1: "Urbana", 2: "Rural"}
    )

    analises = [
        (
            "Renda familiar",
            ["Sem renda", "Até 1 SM", "1 a 2 SM", "2 a 3 SM", "3 a 5 SM", "5 a 10 SM", "Mais de 10 SM"],
            "renda",
        ),
        ("Escolaridade da mãe", list(ESCOLARIDADE_CURTA.values()), "escolaridade_mae"),
        ("Rede da escola", ["Federal", "Estadual", "Municipal", "Privada", "Não informada"], "rede"),
        ("Região", ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul", "Não informada"], "regiao"),
        ("Internet em casa", ["Não", "Sim"], "internet"),
        ("Computador em casa", ["Nenhum", "Um", "Dois ou mais"], "computador"),
        ("Localização da escola", ["Urbana", "Rural"], "localizacao"),
    ]

    grafico_distribuicao(df, corte, args.saida / "distribuicao_media.png")
    md = [
        "# Análise exploratória – ENEM 2023",
        "",
        f"- Amostra: {len(df):,} concluintes presentes nas 4 provas e com redação válida".replace(",", "."),
        f"- Média das 5 notas: {df['media_notas'].mean():.1f} · corte do quartil inferior: **{corte:.1f}**",
        f"- Taxa geral no quartil inferior: {taxa_geral:.1%} (por definição, cerca de 25%)",
        "",
        "Gerado por `python -m ml.eda`. SM = salário mínimo de 2023 (R$ 1.320).",
        "",
        "![Distribuição da média](distribuicao_media.png)",
        "",
    ]
    for coluna, ordem, arquivo in analises:
        tabela = taxa_por(df, coluna, ordem)
        grafico_barras(
            tabela, f"Alunos no quartil inferior por {coluna.lower()}", taxa_geral, args.saida / f"{arquivo}.png"
        )
        md += [f"## {coluna}", "", f"![{coluna}]({arquivo}.png)", "", *tabela_md(tabela, coluna), ""]

    ausentes = df[[*c.VARIAVEIS]].isna().mean().sort_values(ascending=False)
    md += ["## Dados ausentes por variável", "", "| Variável | % ausente |", "| --- | --- |"]
    md += [f"| {nome} | {valor:.1%} |" for nome, valor in ausentes.items()]
    md += [
        "",
        "Observação: as variáveis da escola (rede, localização, UF) ficam vazias quando o aluno não informou a escola;",
        "o modelo trata isso como a categoria “não informada”.",
    ]
    (args.saida / "README.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"EDA salva em {args.saida}/ ({len(analises) + 1} gráficos e README.md)")


if __name__ == "__main__":
    main()
