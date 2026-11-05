"""Treina e avalia os modelos de risco a partir da amostra do ENEM 2023.

Uso:
    python -m ml.treinar
    python -m ml.treinar --amostra data/amostra_enem_2023.parquet --amostra-grid 100000
    python -m ml.treinar --modelos regressao_logistica mlp --teste-regiao Nordeste

Etapas:
1. Divide treino (70%), validação (10%) e teste (20%), estratificado.
2. Calcula o corte do quartil inferior SÓ no treino e cria o alvo.
3. Ajusta cada modelo com GridSearchCV (5 folds, AUC) no treino.
4. Escolhe o limiar de decisão na validação (maior F1).
5. Avalia no teste e por grupo de cor/raça e sexo (análise de viés).
6. Salva o melhor modelo em models/pipeline.pkl, com models/metadados.json
   e um resumo em models/relatorio_treino.md para o relatório da sprint.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.base import clone
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier

from . import colunas_2023 as c
from .features import ENTRADAS, construir_pipeline, renomear_microdados
from .preparar_dados import carregar

SEMENTE = c.RANDOM_STATE

MODELOS = {
    "regressao_logistica": (
        LogisticRegression(max_iter=2000),
        {"modelo__C": [0.1, 1.0, 10.0]},
    ),
    "arvore_decisao": (
        DecisionTreeClassifier(random_state=SEMENTE),
        {"modelo__max_depth": [4, 8, 12], "modelo__min_samples_leaf": [50, 200]},
    ),
    "random_forest": (
        RandomForestClassifier(n_estimators=200, n_jobs=-1, random_state=SEMENTE),
        {"modelo__max_depth": [10, 16], "modelo__min_samples_leaf": [10, 50]},
    ),
    "gradient_boosting": (
        HistGradientBoostingClassifier(random_state=SEMENTE),
        {"modelo__learning_rate": [0.05, 0.1], "modelo__max_leaf_nodes": [31, 63]},
    ),
    "mlp": (
        MLPClassifier(early_stopping=True, max_iter=200, random_state=SEMENTE),
        {"modelo__hidden_layer_sizes": [(64, 32), (128, 64)], "modelo__alpha": [1e-4, 1e-3]},
    ),
}


def preparar(caminho: Path) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    df = renomear_microdados(carregar(caminho))
    entradas = [col for col in [*ENTRADAS, *c.BENS] if col in df.columns]
    vies = df[[col for col in c.VARIAVEIS_ANALISE_VIES if col in df.columns]]
    return df[entradas], df["media_notas"].astype(float), vies


def limiar_maior_f1(y: np.ndarray, prob: np.ndarray) -> float:
    precisao, revocacao, limiares = precision_recall_curve(y, prob)
    f1 = 2 * precisao * revocacao / np.clip(precisao + revocacao, 1e-9, None)
    return float(limiares[int(np.argmax(f1[:-1]))])


def metricas(y: np.ndarray, prob: np.ndarray, limiar: float) -> dict:
    pred = (prob >= limiar).astype(int)
    vn, fp, fn, vp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {
        "auc": round(float(roc_auc_score(y, prob)), 4) if len(np.unique(y)) > 1 else None,
        "f1": round(float(f1_score(y, pred, zero_division=0)), 4),
        "precisao": round(float(precision_score(y, pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y, pred, zero_division=0)), 4),
        "acuracia": round(float(accuracy_score(y, pred)), 4),
        "matriz_confusao": {"vn": int(vn), "fp": int(fp), "fn": int(fn), "vp": int(vp)},
    }


def analise_vies(vies: pd.DataFrame, y: np.ndarray, prob: np.ndarray, limiar: float) -> dict:
    pred = prob >= limiar
    resultado: dict[str, dict] = {}
    for coluna in vies.columns:
        grupos = {}
        for valor, idx in vies.groupby(vies[coluna].astype(str)).groups.items():
            pos = vies.index.get_indexer(idx)
            yy, pp = y[pos], pred[pos]
            if len(pos) < 30:
                continue
            negativos = (yy == 0).sum()
            grupos[valor] = {
                "n": int(len(pos)),
                "taxa_real_risco": round(float(yy.mean()), 4),
                "taxa_prevista_risco": round(float(pp.mean()), 4),
                "recall": round(float(recall_score(yy, pp, zero_division=0)), 4),
                "falso_positivo": round(float((pp & (yy == 0)).sum() / negativos), 4) if negativos else None,
            }
        resultado[coluna] = grupos
    return resultado


def perfil_referencia(X: pd.DataFrame) -> dict:
    """Respostas mais comuns no treino: base para explicar cada previsão (ver api/modelo.py)."""
    referencia: dict = {}
    for coluna in X.columns:
        moda = X[coluna].dropna().mode()
        valor = None if moda.empty else moda.iloc[0]
        referencia[coluna] = valor.item() if hasattr(valor, "item") else valor
    return referencia


def teste_por_regiao(X, media, regiao_fora: str, modelo, params) -> dict:
    regioes = X["uf_escola"].astype("string").str.upper().map(c.REGIAO_POR_UF)
    dentro = regioes != regiao_fora
    corte = float(media[dentro].quantile(c.QUANTIL_RISCO))
    y = (media < corte).astype(int).to_numpy()
    pipe = construir_pipeline(clone(modelo)).set_params(**params)
    pipe.fit(X[dentro], y[dentro.to_numpy()])
    prob = pipe.predict_proba(X[~dentro])[:, 1]
    return {
        "regiao_teste": regiao_fora,
        "n_teste": int((~dentro).sum()),
        "auc": round(float(roc_auc_score(y[~dentro.to_numpy()], prob)), 4),
    }


@dataclass
class Divisao:
    """Conjuntos de ajuste (treino), validação e teste, com o alvo já calculado."""

    X_ajuste: pd.DataFrame
    y_ajuste: np.ndarray
    X_validacao: pd.DataFrame
    y_validacao: np.ndarray
    X_teste: pd.DataFrame
    y_teste: np.ndarray
    idx_teste: pd.Index
    corte: float


@dataclass
class ModeloTreinado:
    pipeline: Pipeline
    parametros: dict
    limiar: float
    prob_teste: np.ndarray
    resultado: dict


def dividir(X: pd.DataFrame, media: pd.Series) -> Divisao:
    """70% ajuste / 10% validação / 20% teste, estratificado por região e tipo de escola.
    O corte do quartil é calculado só no conjunto de ajuste (evita vazamento de informação)."""
    regiao = X["uf_escola"].astype("string").str.upper().map(c.REGIAO_POR_UF).fillna("NI")
    estrato = regiao + "|" + X["tipo_escola"].astype(str)
    idx_treino, idx_teste = train_test_split(X.index, test_size=0.2, stratify=estrato, random_state=SEMENTE)
    idx_ajuste, idx_val = train_test_split(
        idx_treino, test_size=0.125, stratify=estrato[idx_treino], random_state=SEMENTE
    )
    corte = float(media[idx_ajuste].quantile(c.QUANTIL_RISCO))
    y = (media < corte).astype(int)
    return Divisao(
        X.loc[idx_ajuste],
        y[idx_ajuste].to_numpy(),
        X.loc[idx_val],
        y[idx_val].to_numpy(),
        X.loc[idx_teste],
        y[idx_teste].to_numpy(),
        idx_teste,
        corte,
    )


def treinar_modelo(nome: str, d: Divisao, amostra_grid: int) -> ModeloTreinado:
    """GridSearchCV numa parte do ajuste, treino final no ajuste todo, limiar na validação, métricas no teste."""
    modelo, grade = MODELOS[nome]
    inicio = time.time()
    if len(d.X_ajuste) > amostra_grid:
        pos_grid, _ = train_test_split(
            np.arange(len(d.X_ajuste)), train_size=amostra_grid, stratify=d.y_ajuste, random_state=SEMENTE
        )
    else:
        pos_grid = np.arange(len(d.X_ajuste))
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEMENTE)
    busca = GridSearchCV(construir_pipeline(clone(modelo)), grade, scoring="roc_auc", cv=cv, n_jobs=-1)
    busca.fit(d.X_ajuste.iloc[pos_grid], d.y_ajuste[pos_grid])

    final = construir_pipeline(clone(modelo)).set_params(**busca.best_params_)
    final.fit(d.X_ajuste, d.y_ajuste)
    prob_val = final.predict_proba(d.X_validacao)[:, 1]
    limiar = limiar_maior_f1(d.y_validacao, prob_val)
    prob_te = final.predict_proba(d.X_teste)[:, 1]

    resultado = {
        "melhores_parametros": {
            k.replace("modelo__", ""): (list(v) if isinstance(v, tuple) else v) for k, v in busca.best_params_.items()
        },
        "auc_validacao_cruzada": round(float(busca.best_score_), 4),
        "auc_validacao": round(float(roc_auc_score(d.y_validacao, prob_val)), 4),
        "limiar": round(limiar, 4),
        "teste": metricas(d.y_teste, prob_te, limiar),
        "segundos": round(time.time() - inicio, 1),
    }
    return ModeloTreinado(final, busca.best_params_, limiar, prob_te, resultado)


def montar_metadados(
    escolhido: str, d: Divisao, total: int, treinados: dict[str, ModeloTreinado], vies: dict, extra: dict | None
) -> dict:
    agora = datetime.now(UTC)
    melhor = treinados[escolhido]
    return {
        "modelo": escolhido,
        "versao": f"{escolhido}-{agora:%Y%m%d}",
        "treinado_em": agora.isoformat(timespec="seconds"),
        "versao_sklearn": sklearn.__version__,
        "ano_dados": c.ANO,
        "amostra": {
            "total": total,
            "ajuste": len(d.X_ajuste),
            "validacao": len(d.X_validacao),
            "teste": len(d.X_teste),
        },
        "alvo": {
            "descricao": "média das 5 notas no quartil inferior",
            "corte_media": round(d.corte, 2),
            "taxa_risco_treino": round(float(d.y_ajuste.mean()), 4),
        },
        "entradas": list(d.X_ajuste.columns),
        "limiar_decisao": round(melhor.limiar, 4),
        "referencia": perfil_referencia(d.X_ajuste),
        "resultados": {nome: t.resultado for nome, t in treinados.items()},
        "analise_vies": vies,
        "teste_regiao": extra,
    }


def salvar_resultados(pasta: Path, pipeline: Pipeline, metadados: dict) -> None:
    pasta.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, pasta / "pipeline.pkl")
    texto = json.dumps(metadados, ensure_ascii=False, indent=2, default=str)
    (pasta / "metadados.json").write_text(texto, encoding="utf-8")
    (pasta / "relatorio_treino.md").write_text(relatorio(metadados), encoding="utf-8")


def ler_argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--amostra", type=Path, default=Path("data/amostra_enem_2023.parquet"))
    parser.add_argument("--saida", type=Path, default=Path("models"))
    parser.add_argument("--modelos", nargs="+", choices=list(MODELOS), default=list(MODELOS))
    parser.add_argument(
        "--amostra-grid",
        type=int,
        default=100_000,
        help="Linhas do treino usadas no GridSearchCV (o modelo final usa o treino todo).",
    )
    parser.add_argument(
        "--escolher", choices=list(MODELOS), help="Força o modelo salvo (padrão: maior AUC na validação)."
    )
    parser.add_argument(
        "--teste-regiao",
        choices=sorted(set(c.REGIAO_POR_UF.values())),
        help="Teste extra: treina sem esta região e avalia nela.",
    )
    return parser.parse_args()


def main() -> None:
    args = ler_argumentos()
    X, media, vies = preparar(args.amostra)
    print(f"Amostra: {len(X):,} alunos".replace(",", "."))

    divisao = dividir(X, media)
    print(f"Corte do quartil inferior (treino): média < {divisao.corte:.1f}")

    treinados: dict[str, ModeloTreinado] = {}
    for nome in args.modelos:
        treinado = treinar_modelo(nome, divisao, args.amostra_grid)
        treinados[nome] = treinado
        r = treinado.resultado
        print(
            f"  {nome:<20} AUC CV {r['auc_validacao_cruzada']:.3f} · AUC teste {r['teste']['auc']:.3f} · "
            f"F1 {r['teste']['f1']:.3f} · recall {r['teste']['recall']:.3f} · {r['segundos']}s"
        )

    escolhido = args.escolher or max(treinados, key=lambda n: treinados[n].resultado["auc_validacao"])
    melhor = treinados[escolhido]
    print(f"\nModelo escolhido: {escolhido}")

    vies_resultado = {}
    if not vies.empty:
        vies_teste = vies.loc[divisao.idx_teste].reset_index(drop=True)
        vies_resultado = analise_vies(vies_teste, divisao.y_teste, melhor.prob_teste, melhor.limiar)

    extra = None
    if args.teste_regiao:
        extra = teste_por_regiao(X, media, args.teste_regiao, MODELOS[escolhido][0], melhor.parametros)
        print(f"Teste sem a região {args.teste_regiao}: AUC {extra['auc']:.3f}")

    metadados = montar_metadados(escolhido, divisao, len(X), treinados, vies_resultado, extra)
    salvar_resultados(args.saida, melhor.pipeline, metadados)
    print(f"Salvo em {args.saida}/pipeline.pkl, metadados.json e relatorio_treino.md")


def _milhar(numero: int) -> str:
    return f"{numero:,}".replace(",", ".")


def _linha_tabela(*celulas) -> str:
    return "| " + " | ".join(str(c) for c in celulas) + " |"


def relatorio(m: dict) -> str:
    """Resumo do treino em Markdown, pronto para o relatório da sprint."""
    a = m["amostra"]
    linhas = [
        f"# Relatório de treino – {m['versao']}",
        "",
        f"- Dados: ENEM {m['ano_dados']} · {_milhar(a['total'])} concluintes",
        f"- Divisão: ajuste {_milhar(a['ajuste'])} · validação {_milhar(a['validacao'])} · teste {_milhar(a['teste'])}",
        f"- Alvo: {m['alvo']['descricao']} (média < {m['alvo']['corte_media']})",
        f"- Modelo escolhido: **{m['modelo']}**",
        "",
        "## Comparação dos modelos (conjunto de teste)",
        "",
        _linha_tabela("Modelo", "AUC CV", "AUC teste", "F1", "Precisão", "Recall", "Limiar"),
        _linha_tabela(*["---"] * 7),
    ]
    for nome, r in m["resultados"].items():
        t = r["teste"]
        linhas.append(
            _linha_tabela(nome, r["auc_validacao_cruzada"], t["auc"], t["f1"], t["precisao"], t["recall"], r["limiar"])
        )
    if m.get("teste_regiao"):
        e = m["teste_regiao"]
        linhas += ["", f"Teste sem a região **{e['regiao_teste']}** ({_milhar(e['n_teste'])} alunos): AUC {e['auc']}"]
    if m.get("analise_vies"):
        linhas += ["", "## Análise de viés (modelo escolhido, teste)", ""]
        for coluna, grupos in m["analise_vies"].items():
            linhas += [
                f"**{coluna}**",
                "",
                _linha_tabela("Grupo", "n", "Risco real", "Risco previsto", "Recall", "Falso positivo"),
                _linha_tabela(*["---"] * 6),
            ]
            for g, v in grupos.items():
                linhas.append(
                    _linha_tabela(
                        g, v["n"], v["taxa_real_risco"], v["taxa_prevista_risco"], v["recall"], v["falso_positivo"]
                    )
                )
            linhas.append("")
        linhas.append("Códigos dos grupos conforme o dicionário do ENEM 2023 (TP_COR_RACA, TP_SEXO).")
    return "\n".join(linhas) + "\n"


if __name__ == "__main__":
    main()
