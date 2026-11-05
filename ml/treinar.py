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
from datetime import datetime, timezone
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
    return {"regiao_teste": regiao_fora, "n_teste": int((~dentro).sum()),
            "auc": round(float(roc_auc_score(y[~dentro.to_numpy()], prob)), 4)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--amostra", type=Path, default=Path("data/amostra_enem_2023.parquet"))
    parser.add_argument("--saida", type=Path, default=Path("models"))
    parser.add_argument("--modelos", nargs="+", choices=list(MODELOS), default=list(MODELOS))
    parser.add_argument("--amostra-grid", type=int, default=100_000,
                        help="Linhas do treino usadas no GridSearchCV (o modelo final usa o treino todo).")
    parser.add_argument("--escolher", choices=list(MODELOS), help="Força o modelo salvo (padrão: maior AUC na validação).")
    parser.add_argument("--teste-regiao", choices=sorted(set(c.REGIAO_POR_UF.values())),
                        help="Teste extra: treina sem esta região e avalia nela.")
    args = parser.parse_args()

    X, media, vies = preparar(args.amostra)
    print(f"Amostra: {len(X):,} alunos".replace(",", "."))

    estrato = X["uf_escola"].astype("string").str.upper().map(c.REGIAO_POR_UF).fillna("NI") + "|" + X["tipo_escola"].astype(str)
    idx_treino, idx_teste = train_test_split(X.index, test_size=0.2, stratify=estrato, random_state=SEMENTE)
    idx_ajuste, idx_val = train_test_split(idx_treino, test_size=0.125, stratify=estrato[idx_treino], random_state=SEMENTE)

    corte = float(media[idx_ajuste].quantile(c.QUANTIL_RISCO))
    y = (media < corte).astype(int)
    print(f"Corte do quartil inferior (treino): média < {corte:.1f}")

    X_aj, y_aj = X.loc[idx_ajuste], y[idx_ajuste].to_numpy()
    X_val, y_val = X.loc[idx_val], y[idx_val].to_numpy()
    X_te, y_te = X.loc[idx_teste], y[idx_teste].to_numpy()

    if len(X_aj) > args.amostra_grid:
        idx_grid, _ = train_test_split(X_aj.index, train_size=args.amostra_grid, stratify=y_aj, random_state=SEMENTE)
    else:
        idx_grid = X_aj.index
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEMENTE)

    resultados = {}
    pipelines = {}
    for nome in args.modelos:
        modelo, grade = MODELOS[nome]
        inicio = time.time()
        busca = GridSearchCV(construir_pipeline(clone(modelo)), grade, scoring="roc_auc", cv=cv, n_jobs=-1)
        busca.fit(X_aj.loc[idx_grid], y[idx_grid])
        final = construir_pipeline(clone(modelo)).set_params(**busca.best_params_)
        final.fit(X_aj, y_aj)
        prob_val = final.predict_proba(X_val)[:, 1]
        limiar = limiar_maior_f1(y_val, prob_val)
        prob_te = final.predict_proba(X_te)[:, 1]
        resultados[nome] = {
            "melhores_parametros": {k.replace("modelo__", ""): (list(v) if isinstance(v, tuple) else v)
                                    for k, v in busca.best_params_.items()},
            "auc_validacao_cruzada": round(float(busca.best_score_), 4),
            "auc_validacao": round(float(roc_auc_score(y_val, prob_val)), 4),
            "limiar": round(limiar, 4),
            "teste": metricas(y_te, prob_te, limiar),
            "segundos": round(time.time() - inicio, 1),
        }
        pipelines[nome] = (final, prob_te, limiar, busca.best_params_)
        r = resultados[nome]
        print(f"  {nome:<20} AUC CV {r['auc_validacao_cruzada']:.3f} · AUC teste {r['teste']['auc']:.3f} · "
              f"F1 {r['teste']['f1']:.3f} · recall {r['teste']['recall']:.3f} · {r['segundos']}s")

    escolhido = args.escolher or max(resultados, key=lambda n: resultados[n]["auc_validacao"])
    final, prob_te, limiar, params = pipelines[escolhido]
    print(f"\nModelo escolhido: {escolhido}")

    vies_resultado = analise_vies(vies.loc[idx_teste].reset_index(drop=True), y_te, prob_te, limiar) if not vies.empty else {}
    extra = None
    if args.teste_regiao:
        extra = teste_por_regiao(X, media, args.teste_regiao, MODELOS[escolhido][0], params)
        print(f"Teste sem a região {args.teste_regiao}: AUC {extra['auc']:.3f}")

    args.saida.mkdir(parents=True, exist_ok=True)
    joblib.dump(final, args.saida / "pipeline.pkl")
    metadados = {
        "modelo": escolhido,
        "versao": f"{escolhido}-{datetime.now(timezone.utc):%Y%m%d}",
        "treinado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "versao_sklearn": sklearn.__version__,
        "ano_dados": c.ANO,
        "amostra": {"total": len(X), "ajuste": len(idx_ajuste), "validacao": len(idx_val), "teste": len(idx_teste)},
        "alvo": {"descricao": "média das 5 notas no quartil inferior", "corte_media": round(corte, 2),
                 "taxa_risco_treino": round(float(y_aj.mean()), 4)},
        "entradas": list(X.columns),
        "limiar_decisao": round(limiar, 4),
        "referencia": perfil_referencia(X_aj),
        "resultados": resultados,
        "analise_vies": vies_resultado,
        "teste_regiao": extra,
    }
    (args.saida / "metadados.json").write_text(json.dumps(metadados, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    (args.saida / "relatorio_treino.md").write_text(relatorio(metadados), encoding="utf-8")
    print(f"Salvo em {args.saida}/pipeline.pkl, metadados.json e relatorio_treino.md")


def relatorio(m: dict) -> str:
    linhas = [
        f"# Relatório de treino – {m['versao']}",
        "",
        f"- Dados: ENEM {m['ano_dados']} · " + f"{m['amostra']['total']:,} concluintes".replace(",", "."),
        f"- Divisão: ajuste {m['amostra']['ajuste']:,} · validação {m['amostra']['validacao']:,} · teste {m['amostra']['teste']:,}".replace(",", "."),
        f"- Alvo: {m['alvo']['descricao']} (média < {m['alvo']['corte_media']})",
        f"- Modelo escolhido: **{m['modelo']}** (maior AUC na validação)",
        "",
        "## Comparação dos modelos (conjunto de teste)",
        "",
        "| Modelo | AUC CV | AUC teste | F1 | Precisão | Recall | Limiar |",
        "|---|---|---|---|---|---|---|",
    ]
    for nome, r in m["resultados"].items():
        t = r["teste"]
        linhas.append(f"| {nome} | {r['auc_validacao_cruzada']} | {t['auc']} | {t['f1']} | {t['precisao']} | {t['recall']} | {r['limiar']} |")
    if m.get("teste_regiao"):
        e = m["teste_regiao"]
        linhas += ["", f"Teste sem a região **{e['regiao_teste']}** ({e['n_teste']:,} alunos): AUC {e['auc']}".replace(",", ".")]
    if m.get("analise_vies"):
        linhas += ["", "## Análise de viés (modelo escolhido, teste)", ""]
        for coluna, grupos in m["analise_vies"].items():
            linhas += [f"**{coluna}**", "", "| Grupo | n | Risco real | Risco previsto | Recall | Falso positivo |", "|---|---|---|---|---|---|"]
            for g, v in grupos.items():
                linhas.append(f"| {g} | {v['n']} | {v['taxa_real_risco']} | {v['taxa_prevista_risco']} | {v['recall']} | {v['falso_positivo']} |")
            linhas.append("")
        linhas.append("Códigos dos grupos conforme o dicionário do ENEM 2023 (TP_COR_RACA, TP_SEXO).")
    return "\n".join(linhas) + "\n"


if __name__ == "__main__":
    main()
