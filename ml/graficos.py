"""Gráficos dos resultados do treino (lidos de models/metadados.json).

Uso:
    python -m ml.graficos
    python -m ml.graficos --metadados models/metadados.json --saida docs/resultados

Também é chamado no fim de ml/treinar.py. Precisa do matplotlib (requirements-dev.txt).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from . import colunas_2023 as c  # noqa: E402

COR = "#4f46e5"  # série principal (com / modelo escolhido)
COR_2 = "#94a3b8"  # série de comparação (sem / outros modelos)
COR_REAL = "#f59e0b"  # valor real
TEXTO = "#334155"
GRADE = "#e2e8f0"

NOMES_MODELOS = {
    "regressao_logistica": "Regressão logística",
    "arvore_decisao": "Árvore de decisão",
    "random_forest": "Random forest",
    "gradient_boosting": "Gradient boosting",
    "mlp": "Rede neural (MLP)",
}
ORDEM_COR = ["1", "2", "3", "4", "5", "0"]
ROTULO_COR = {**c.COR_RACA, "0": "Não declarada"}


def _estilo(ax, titulo: str, ylabel: str | None = None) -> None:
    ax.set_title(titulo, loc="left", fontsize=11, color=TEXTO, fontweight="bold", pad=10)
    if ylabel:
        ax.set_ylabel(ylabel, color=TEXTO, fontsize=9)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(GRADE)
    ax.tick_params(colors=TEXTO, labelsize=9, length=0)
    ax.grid(axis="y", color=GRADE, zorder=0)
    ax.set_axisbelow(True)


def _rotular(ax, barras, formato: str = "{:.1f}") -> None:
    for barra in barras:
        altura = barra.get_height()
        ax.annotate(
            formato.format(altura),
            (barra.get_x() + barra.get_width() / 2, altura),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            fontsize=8.5,
            color=TEXTO,
        )


def _barras_agrupadas(ax, categorias, series: dict[str, tuple[list[float], str]], formato="{:.1f}") -> None:
    x = np.arange(len(categorias))
    largura = 0.8 / len(series)
    for i, (rotulo, (valores, cor)) in enumerate(series.items()):
        barras = ax.bar(x + (i - (len(series) - 1) / 2) * largura, valores, largura * 0.92, label=rotulo, color=cor)
        _rotular(ax, barras, formato)
    ax.set_xticks(x, categorias)


def _salvar(fig, caminho: Path) -> Path:
    fig.tight_layout()
    fig.savefig(caminho, dpi=150, facecolor="white")
    plt.close(fig)
    return caminho


def _pct(valor: float | None) -> float:
    return 0.0 if valor is None else valor * 100


def grafico_regiao(t: dict, pasta: Path) -> Path:
    r = t["regiao"]
    com, sem = r["com_regiao"]["na_regiao"], r["sem_regiao"]["na_regiao"]
    nome = r["regiao"]
    fig, eixos = plt.subplots(1, 3, figsize=(13, 4.2), gridspec_kw={"width_ratios": [1, 1.6, 1.3]})

    ax = eixos[0]
    barras = ax.bar([f"Com o\n{nome}", f"Sem o\n{nome}"], [com["auc"], sem["auc"]], color=[COR, COR_2], width=0.6)
    _rotular(ax, barras, "{:.3f}")
    ax.set_ylim(0.5, 1)
    _estilo(ax, "AUC nos alunos do " + nome)

    ax = eixos[1]
    _barras_agrupadas(
        ax,
        ["F1", "Recall", "Falso positivo"],
        {
            f"Treino com o {nome}": ([_pct(com["f1"]), _pct(com["recall"]), _pct(com["falso_positivo"])], COR),
            f"Treino sem o {nome}": ([_pct(sem["f1"]), _pct(sem["recall"]), _pct(sem["falso_positivo"])], COR_2),
        },
    )
    ax.set_ylim(0, 118)
    ax.set_yticks(range(0, 101, 20))
    ax.legend(frameon=False, fontsize=8.5, loc="upper left", ncols=2)
    _estilo(ax, "Acertos e erros (%)")

    ax = eixos[2]
    barras = ax.bar(
        ["Real", f"Previsto\ncom o {nome}", f"Previsto\nsem o {nome}"],
        [_pct(com["taxa_real_risco"]), _pct(com["risco_medio_previsto"]), _pct(sem["risco_medio_previsto"])],
        color=[COR_REAL, COR, COR_2],
        width=0.6,
    )
    _rotular(ax, barras, "{:.1f}%")
    ax.set_ylim(0, max(b.get_height() for b in barras) * 1.25)
    _estilo(ax, "Alunos em risco (%)")

    fig.suptitle(
        f"Treino com e sem o {nome} · avaliação nos {r['n_teste_regiao']:,} alunos do {nome} no teste".replace(
            ",", "."
        ),
        x=0.01,
        ha="left",
        fontsize=12.5,
        fontweight="bold",
        color=TEXTO,
    )
    return _salvar(fig, pasta / "01_regiao_com_sem.png")


def grafico_cor_sexo(t: dict, pasta: Path) -> Path:
    cs = t["cor_sexo"]
    fig, eixos = plt.subplots(1, 2, figsize=(13, 4.2), gridspec_kw={"width_ratios": [1, 3]})

    ax = eixos[0]
    barras = ax.bar(
        ["Com cor/raça\ne sexo", "Sem cor/raça\ne sexo"],
        [cs["com"]["teste"]["auc"], cs["sem"]["teste"]["auc"]],
        color=[COR, COR_2],
        width=0.6,
    )
    _rotular(ax, barras, "{:.3f}")
    ax.set_ylim(0.5, 1)
    _estilo(ax, "AUC no teste")

    ax = eixos[1]
    com, sem = cs["com"]["vies"].get("cor_raca", {}), cs["sem"]["vies"].get("cor_raca", {})
    grupos = [g for g in ORDEM_COR if g in com and g in sem]
    _barras_agrupadas(
        ax,
        [ROTULO_COR[g] for g in grupos],
        {
            "Com cor/raça e sexo": ([_pct(com[g]["falso_positivo"]) for g in grupos], COR),
            "Sem cor/raça e sexo": ([_pct(sem[g]["falso_positivo"]) for g in grupos], COR_2),
        },
    )
    ax.legend(frameon=False, fontsize=8.5, loc="upper left", ncols=2)
    ax.set_ylim(0, max(_pct(v["falso_positivo"]) for v in [*com.values(), *sem.values()]) * 1.35)
    _estilo(ax, "Falso positivo por cor/raça (%): alunos fora do risco apontados por engano")

    fig.suptitle("Modelo com e sem cor/raça e sexo", x=0.01, ha="left", fontsize=12.5, fontweight="bold", color=TEXTO)
    return _salvar(fig, pasta / "02_cor_sexo_com_sem.png")


def grafico_vies(vies: dict, coluna: str, titulo: str, rotulos: dict, ordem: list[str], caminho: Path) -> Path:
    grupos = [g for g in ordem if g in vies.get(coluna, {})]
    dados = vies[coluna]
    fig, ax = plt.subplots(figsize=(10 if len(grupos) > 3 else 7, 4.2))
    _barras_agrupadas(
        ax,
        [f"{rotulos.get(g, g)}\n(n={dados[g]['n']:,})".replace(",", ".") for g in grupos],
        {
            "Risco real": ([_pct(dados[g]["taxa_real_risco"]) for g in grupos], COR_REAL),
            "Recall": ([_pct(dados[g]["recall"]) for g in grupos], COR),
            "Falso positivo": ([_pct(dados[g]["falso_positivo"]) for g in grupos], COR_2),
        },
    )
    ax.set_ylim(0, 118)
    ax.set_yticks(range(0, 101, 20))
    ax.legend(frameon=False, fontsize=8.5, loc="upper left", ncols=3)
    _estilo(ax, titulo, "%")
    return _salvar(fig, caminho)


def grafico_auc_modelos(m: dict, pasta: Path) -> Path:
    nomes = sorted(m["resultados"], key=lambda n: m["resultados"][n]["teste"]["auc"])
    aucs = [m["resultados"][n]["teste"]["auc"] for n in nomes]
    fig, ax = plt.subplots(figsize=(8, 0.55 * len(nomes) + 1.4))
    barras = ax.barh(
        [NOMES_MODELOS.get(n, n) for n in nomes], aucs, color=[COR if n == m["modelo"] else COR_2 for n in nomes]
    )
    for barra, auc in zip(barras, aucs, strict=True):
        ax.annotate(
            f"{auc:.3f}",
            (auc, barra.get_y() + barra.get_height() / 2),
            xytext=(4, 0),
            textcoords="offset points",
            va="center",
            fontsize=9,
            color=TEXTO,
        )
    ax.set_xlim(0.5, 0.82)
    _estilo(ax, "AUC no conjunto de teste (em destaque: modelo escolhido)")
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color=GRADE)
    return _salvar(fig, pasta / "05_auc_modelos.png")


def grafico_roc(m: dict, pasta: Path) -> Path:
    fig, ax = plt.subplots(figsize=(6.2, 5.6))
    cores = ["#a5b4fc", "#7dd3fc", "#fcd34d", "#86efac"]
    outros = iter(cores)
    for nome, curva in m["curvas_roc"].items():
        escolhido = nome == m["modelo"]
        auc = m["resultados"][nome]["teste"]["auc"]
        ax.plot(
            curva["fpr"],
            curva["tpr"],
            color=COR if escolhido else next(outros, COR_2),
            linewidth=2.6 if escolhido else 1.4,
            label=f"{NOMES_MODELOS.get(nome, nome)} ({auc:.3f})",
            zorder=3 if escolhido else 2,
        )
    ax.plot([0, 1], [0, 1], color=COR_2, linestyle="--", linewidth=1, label="Acaso (0,500)")
    ax.set_xlabel("Taxa de falso positivo", color=TEXTO, fontsize=9)
    ax.set_ylabel("Taxa de verdadeiro positivo (recall)", color=TEXTO, fontsize=9)
    ax.legend(frameon=False, fontsize=8.5, loc="lower right")
    _estilo(ax, "Curvas ROC no conjunto de teste")
    ax.grid(axis="x", color=GRADE)
    return _salvar(fig, pasta / "06_curvas_roc.png")


def grafico_matriz(m: dict, pasta: Path) -> Path:
    mc = m["resultados"][m["modelo"]]["teste"]["matriz_confusao"]
    matriz = np.array([[mc["vn"], mc["fp"]], [mc["fn"], mc["vp"]]])
    fig, ax = plt.subplots(figsize=(5.6, 4.8))
    ax.imshow(matriz, cmap="Purples")
    total = matriz.sum()
    for i in range(2):
        for j in range(2):
            ax.text(
                j,
                i,
                f"{matriz[i, j]:,}\n{matriz[i, j] / total:.1%}".replace(",", "."),
                ha="center",
                va="center",
                fontsize=11,
                color="white" if matriz[i, j] > matriz.max() / 2 else TEXTO,
            )
    ax.set_xticks([0, 1], ["Fora do risco", "Em risco"])
    ax.set_yticks([0, 1], ["Fora do risco", "Em risco"])
    ax.set_xlabel("Previsto pelo modelo", color=TEXTO)
    ax.set_ylabel("Real", color=TEXTO)
    ax.tick_params(colors=TEXTO, length=0)
    ax.set_title(
        f"Matriz de confusão · {NOMES_MODELOS.get(m['modelo'], m['modelo'])}\n"
        f"limiar de decisão {m['limiar_decisao']:.2f}",
        fontsize=11,
        color=TEXTO,
        fontweight="bold",
    )
    for lado in ax.spines.values():
        lado.set_visible(False)
    return _salvar(fig, pasta / "07_matriz_confusao.png")


def gerar_graficos(m: dict, pasta: Path) -> list[Path]:
    pasta.mkdir(parents=True, exist_ok=True)
    arquivos: list[Path] = []
    if m.get("testes_iniciais"):
        arquivos += [grafico_regiao(m["testes_iniciais"], pasta), grafico_cor_sexo(m["testes_iniciais"], pasta)]
    if m.get("analise_vies"):
        nome = NOMES_MODELOS.get(m["modelo"], m["modelo"])
        arquivos.append(
            grafico_vies(
                m["analise_vies"],
                "cor_raca",
                f"Resultado por cor/raça · {nome}",
                ROTULO_COR,
                ORDEM_COR,
                pasta / "03_vies_cor_raca.png",
            )
        )
        arquivos.append(
            grafico_vies(
                m["analise_vies"],
                "sexo",
                f"Resultado por sexo · {nome}",
                c.SEXO,
                ["F", "M"],
                pasta / "04_vies_sexo.png",
            )
        )
    arquivos.append(grafico_auc_modelos(m, pasta))
    if m.get("curvas_roc"):
        arquivos.append(grafico_roc(m, pasta))
    arquivos.append(grafico_matriz(m, pasta))
    return arquivos


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--metadados", type=Path, default=Path("models/metadados.json"))
    parser.add_argument("--saida", type=Path, default=Path("docs/resultados"))
    args = parser.parse_args()
    metadados = json.loads(args.metadados.read_text(encoding="utf-8"))
    for arquivo in gerar_graficos(metadados, args.saida):
        print(arquivo)


if __name__ == "__main__":
    main()
