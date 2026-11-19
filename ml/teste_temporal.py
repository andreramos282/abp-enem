"""Teste em outro ano: aplica o modelo treinado com o ENEM 2023 nos microdados de outro ano (ex.: 2022).

Uso:
    python -m ml.teste_temporal data/MICRODADOS_ENEM_2022.csv --ano 2022

Mostra se o modelo continua funcionando com alunos que ele nunca viu, de outra edição da prova.

- Mesma população do treino: concluintes presentes nas 4 provas e com redação válida.
- O alvo usa o quartil inferior DO PRÓPRIO ANO, porque a escala das notas muda entre edições.
- As faixas de renda do questionário são definidas em salários mínimos nos dois anos, então o
  mesmo código representa a mesma faixa em salários mínimos (confira no dicionário do ano usado).
- O ENEM 2022 tem o questionário e as notas no mesmo arquivo, como o 2023. A partir de 2024 o INEP
  separa os arquivos sem chave em comum, então este teste não funciona com 2024 ou 2025.

Saída: models/teste_temporal_<ano>.json e docs/resultados/12_teste_temporal_<ano>.png
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np

from . import colunas_2023 as c
from .features import renomear_microdados
from .preparar_dados import ler_populacao
from .treinar import analise_vies, metricas


def avaliar(caminho: Path, ano: int, pasta_modelo: Path, tamanho: int, encoding: str) -> dict:
    metadados = json.loads((pasta_modelo / "metadados.json").read_text(encoding="utf-8"))
    pipeline = joblib.load(pasta_modelo / "pipeline.pkl")

    populacao = ler_populacao(caminho, encoding=encoding)
    if len(populacao) > tamanho:
        populacao = populacao.sample(tamanho, random_state=c.RANDOM_STATE)
    df = renomear_microdados(populacao).reset_index(drop=True)

    corte = float(df["media_notas"].quantile(c.QUANTIL_RISCO))
    y = (df["media_notas"] < corte).astype(int).to_numpy()
    X = df.reindex(columns=metadados["entradas"])
    prob = pipeline.predict_proba(X)[:, 1]
    limiar = metadados["limiar_decisao"]

    vies = df[[col for col in c.VARIAVEIS_ANALISE_VIES if col in df.columns]]
    return {
        "ano": ano,
        "modelo": metadados["versao"],
        "alunos": len(df),
        "corte_media": round(corte, 2),
        "limiar": limiar,
        "teste": metricas(y, prob, limiar),
        "referencia_2023": metadados["resultados"][metadados["modelo"]]["teste"],
        "vies": analise_vies(vies, y, prob, limiar),
    }


def grafico(resultado: dict, caminho: Path) -> Path:
    from .graficos import COR, COR_2, _barras_agrupadas, _estilo, _salvar, plt

    novo, ref = resultado["teste"], resultado["referencia_2023"]
    fig, eixos = plt.subplots(1, 2, figsize=(11, 4.2), gridspec_kw={"width_ratios": [1, 2]})
    ax = eixos[0]
    barras = ax.bar(["ENEM 2023\n(teste)", f"ENEM {resultado['ano']}"], [ref["auc"], novo["auc"]], color=[COR, COR_2])
    for barra in barras:
        ax.annotate(
            f"{barra.get_height():.3f}",
            (barra.get_x() + barra.get_width() / 2, barra.get_height()),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            fontsize=8.5,
        )
    ax.set_ylim(0.5, 1)
    _estilo(ax, "AUC")
    ax = eixos[1]
    _barras_agrupadas(
        ax,
        ["F1", "Recall", "Falso positivo"],
        {
            "ENEM 2023 (teste)": ([ref["f1"] * 100, ref["recall"] * 100, (ref.get("falso_positivo") or 0) * 100], COR),
            f"ENEM {resultado['ano']}": (
                [novo["f1"] * 100, novo["recall"] * 100, (novo.get("falso_positivo") or 0) * 100],
                COR_2,
            ),
        },
    )
    ax.set_ylim(0, 118)
    ax.set_yticks(range(0, 101, 20))
    ax.legend(frameon=False, fontsize=8.5, loc="upper left", ncols=2)
    _estilo(ax, "Acertos e erros (%)")
    fig.suptitle(
        f"Modelo treinado em 2023 aplicado ao ENEM {resultado['ano']} ({resultado['alunos']:,} alunos)".replace(
            ",", "."
        ),
        x=0.01,
        ha="left",
        fontsize=12.5,
        fontweight="bold",
    )
    return _salvar(fig, caminho)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("microdados", type=Path, help="CSV dos microdados de outro ano (ex.: MICRODADOS_ENEM_2022.csv)")
    parser.add_argument("--ano", type=int, default=2022)
    parser.add_argument("--modelo", type=Path, default=Path("models"))
    parser.add_argument("--tamanho", type=int, default=200_000, help="Alunos sorteados para o teste.")
    parser.add_argument("--encoding", default="latin-1")
    parser.add_argument("--graficos", type=Path, default=Path("docs/resultados"))
    args = parser.parse_args()

    resultado = avaliar(args.microdados, args.ano, args.modelo, args.tamanho, args.encoding)
    saida = args.modelo / f"teste_temporal_{args.ano}.json"
    saida.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    t = resultado["teste"]
    print(f"ENEM {args.ano}: {resultado['alunos']} alunos · AUC {t['auc']} · F1 {t['f1']} · recall {t['recall']}")
    print(f"Resultado salvo em {saida}")
    try:
        args.graficos.mkdir(parents=True, exist_ok=True)
        print(grafico(resultado, args.graficos / f"12_teste_temporal_{args.ano}.png"))
    except ImportError:
        print("matplotlib não instalado: gráfico não gerado.")


if __name__ == "__main__":
    np.seterr(all="ignore")
    main()
