"""Treina e avalia os modelos de risco a partir da amostra do ENEM 2023.

Uso:
    python -m ml.treinar
    python -m ml.treinar --amostra data/amostra_enem_2023.parquet --amostra-grid 100000
    python -m ml.treinar --modelos regressao_logistica mlp --escolher mlp --teste-regiao Nordeste

Etapas:
1. Divide treino (70%), validação (10%) e teste (20%), estratificado.
2. Calcula o corte do quartil inferior SÓ no treino e cria o alvo.
3. Testes iniciais, com o mesmo modelo e os mesmos dados de teste:
   a) treino COM e SEM a região escolhida (padrão: Nordeste), avaliando nos alunos dessa região;
   b) treino COM e SEM cor/raça e sexo, comparando desempenho e viés.
4. Ajusta cada modelo com GridSearchCV (5 folds, AUC) no treino.
5. Escolhe o limiar de decisão na validação (maior F1).
6. Avalia no teste e por grupo de cor/raça e sexo (análise de viés).
7. Salva o melhor modelo em models/pipeline.pkl, com models/metadados.json,
   um resumo em models/relatorio_treino.md e os gráficos em docs/resultados/.
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
    roc_curve,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier

from . import avaliacao as av
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


# Parâmetros usados nos testes iniciais (melhores da busca em grade do treino anterior).
PARAMETROS_TESTES = {"mlp": {"modelo__hidden_layer_sizes": (64, 32), "modelo__alpha": 1e-3}}


def preparar(caminho: Path) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    df = renomear_microdados(carregar(caminho))
    entradas = [col for col in [*ENTRADAS, *c.BENS] if col in df.columns]
    vies = df[[col for col in c.VARIAVEIS_ANALISE_VIES if col in df.columns]].copy()
    return df[entradas], df["media_notas"].astype(float), vies


def limiar_maior_f1(y: np.ndarray, prob: np.ndarray) -> float:
    precisao, revocacao, limiares = precision_recall_curve(y, prob)
    f1 = 2 * precisao * revocacao / np.clip(precisao + revocacao, 1e-9, None)
    return float(limiares[int(np.argmax(f1[:-1]))])


def metricas(y: np.ndarray, prob: np.ndarray, limiar: float | np.ndarray) -> dict:
    pred = (prob >= limiar).astype(int)
    vn, fp, fn, vp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {
        "auc": round(float(roc_auc_score(y, prob)), 4) if len(np.unique(y)) > 1 else None,
        "f1": round(float(f1_score(y, pred, zero_division=0)), 4),
        "precisao": round(float(precision_score(y, pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y, pred, zero_division=0)), 4),
        "acuracia": round(float(accuracy_score(y, pred)), 4),
        "taxa_real_risco": round(float(np.mean(y)), 4),
        "risco_medio_previsto": round(float(np.mean(prob)), 4),
        "falso_positivo": round(float(fp / (fp + vn)), 4) if fp + vn else None,
        "matriz_confusao": {"vn": int(vn), "fp": int(fp), "fn": int(fn), "vp": int(vp)},
    }


def analise_vies(vies: pd.DataFrame, y: np.ndarray, prob: np.ndarray, limiar: float | np.ndarray) -> dict:
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


def _juntar_estratos_raros(estrato: pd.Series, minimo: int = 10) -> pd.Series:
    """Estratos com poucos alunos impedem a divisão estratificada: juntam-se ao estrato mais comum."""
    contagem = estrato.value_counts()
    raros = contagem.index[contagem < minimo]
    return estrato.where(~estrato.isin(raros), contagem.index[0])


def dividir(X: pd.DataFrame, media: pd.Series) -> Divisao:
    """70% ajuste / 10% validação / 20% teste, estratificado por região e tipo de escola.
    O corte do quartil é calculado só no conjunto de ajuste (evita vazamento de informação)."""
    regiao = X["uf_escola"].astype("string").str.upper().map(c.REGIAO_POR_UF).fillna("NI")
    estrato = _juntar_estratos_raros(regiao + "|" + X["tipo_escola"].astype(str))
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


def _regiao(X: pd.DataFrame) -> np.ndarray:
    return X["uf_escola"].astype("string").str.upper().map(c.REGIAO_POR_UF).fillna("NI").to_numpy()


def _ajustar(nome: str, params: dict, X: pd.DataFrame, y: np.ndarray, sensiveis: bool = True) -> Pipeline:
    pipe = construir_pipeline(clone(MODELOS[nome][0]), sensiveis=sensiveis).set_params(**params)
    return pipe.fit(X, y)


def testes_iniciais(d: Divisao, vies: pd.DataFrame, nome: str, regiao: str) -> dict:
    """Comparações feitas antes da escolha do modelo, todas avaliadas no MESMO conjunto de teste.

    - Região: um modelo treinado com todo o Brasil e outro treinado SEM a região, os dois avaliados
      nos alunos da região. Mostra se o modelo funciona numa região que ele nunca viu.
    - Cor/raça e sexo: um modelo com e outro sem essas variáveis. Mostra quanto elas acrescentam
      ao desempenho e como mudam o viés.
    O limiar de cada modelo é escolhido na validação, com os mesmos dados usados no treino dele.
    """
    params = PARAMETROS_TESTES.get(nome, {})
    reg_aj, reg_val, reg_te = _regiao(d.X_ajuste), _regiao(d.X_validacao), _regiao(d.X_teste)
    na_regiao = reg_te == regiao
    vies_teste = vies.loc[d.idx_teste].reset_index(drop=True)

    def avaliar(pipe: Pipeline, limiar: float, mascara: np.ndarray | None = None) -> dict:
        prob = pipe.predict_proba(d.X_teste)[:, 1]
        if mascara is None:
            return metricas(d.y_teste, prob, limiar)
        return metricas(d.y_teste[mascara], prob[mascara], limiar)

    inicio = time.time()
    print(f"Testes iniciais com {nome} {params or ''}")

    com = _ajustar(nome, params, d.X_ajuste, d.y_ajuste)
    limiar_com = limiar_maior_f1(d.y_validacao, com.predict_proba(d.X_validacao)[:, 1])

    fora_aj, fora_val = reg_aj != regiao, reg_val != regiao
    sem_regiao = _ajustar(nome, params, d.X_ajuste[fora_aj], d.y_ajuste[fora_aj])
    limiar_sem_regiao = limiar_maior_f1(
        d.y_validacao[fora_val], sem_regiao.predict_proba(d.X_validacao[fora_val])[:, 1]
    )
    regiao_resultado = {
        "regiao": regiao,
        "n_teste_regiao": int(na_regiao.sum()),
        "n_treino_com": len(d.X_ajuste),
        "n_treino_sem": int(fora_aj.sum()),
        "com_regiao": {
            "na_regiao": avaliar(com, limiar_com, na_regiao),
            "outras_regioes": avaliar(com, limiar_com, ~na_regiao),
        },
        "sem_regiao": {
            "na_regiao": avaliar(sem_regiao, limiar_sem_regiao, na_regiao),
            "outras_regioes": avaliar(sem_regiao, limiar_sem_regiao, ~na_regiao),
        },
    }
    a, b = regiao_resultado["com_regiao"]["na_regiao"], regiao_resultado["sem_regiao"]["na_regiao"]
    print(f"  {regiao}: AUC treino com a região {a['auc']:.3f} · sem a região {b['auc']:.3f}")

    sem_sens = _ajustar(nome, params, d.X_ajuste, d.y_ajuste, sensiveis=False)
    limiar_sem_sens = limiar_maior_f1(d.y_validacao, sem_sens.predict_proba(d.X_validacao)[:, 1])
    prob_com = com.predict_proba(d.X_teste)[:, 1]
    prob_sem = sem_sens.predict_proba(d.X_teste)[:, 1]
    sensiveis_resultado = {
        "com": {
            "teste": metricas(d.y_teste, prob_com, limiar_com),
            "vies": analise_vies(vies_teste, d.y_teste, prob_com, limiar_com),
        },
        "sem": {
            "teste": metricas(d.y_teste, prob_sem, limiar_sem_sens),
            "vies": analise_vies(vies_teste, d.y_teste, prob_sem, limiar_sem_sens),
        },
    }
    print(
        f"  Cor/raça e sexo: AUC com {sensiveis_resultado['com']['teste']['auc']:.3f} · "
        f"sem {sensiveis_resultado['sem']['teste']['auc']:.3f} · {time.time() - inicio:.0f}s"
    )
    print("  Com e sem cada região...")
    todas = av.com_e_sem_cada_regiao(d, lambda X, y: _ajustar(nome, params, X, y))
    for reg, v in todas.items():
        print(f"    {reg:<13} AUC com {v['auc_com']:.3f} · sem {v['auc_sem']:.3f}")
    return {
        "modelo": nome,
        "parametros": {k.replace("modelo__", ""): (list(v) if isinstance(v, tuple) else v) for k, v in params.items()},
        "regiao": regiao_resultado,
        "todas_regioes": todas,
        "cor_sexo": sensiveis_resultado,
    }


def curva_roc(y: np.ndarray, prob: np.ndarray, pontos: int = 51) -> dict:
    """Curva ROC resumida (para os gráficos), em pontos fixos de taxa de falso positivo."""
    fpr, tpr, _ = roc_curve(y, prob)
    grade = np.linspace(0, 1, pontos)
    return {"fpr": grade.round(3).tolist(), "tpr": np.interp(grade, fpr, tpr).round(4).tolist()}


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


def avaliacoes_extras(d: Divisao, vies: pd.DataFrame, melhor: ModeloTreinado, com_shap: bool = True) -> dict:
    """Equidade (limiar por cor/raça), calibração e importância das variáveis (SHAP) do modelo escolhido."""
    prob_val = melhor.pipeline.predict_proba(d.X_validacao)[:, 1]
    cor_val = vies.loc[d.X_validacao.index, "cor_raca"]
    vies_teste = vies.loc[d.idx_teste].reset_index(drop=True)
    limiares = av.limiares_equidade(d.y_validacao, prob_val, cor_val, melhor.limiar)
    limiar_linhas = av.limiar_por_linha(vies_teste["cor_raca"], limiares, melhor.limiar)
    extras = {
        "equidade": {
            "criterio": "mesmo recall para todos os grupos de cor/raça (limiar por grupo escolhido na validação)",
            "limiar_geral": round(melhor.limiar, 4),
            "limiares_cor_raca": limiares,
            "teste": metricas(d.y_teste, melhor.prob_teste, limiar_linhas),
            "vies": analise_vies(vies_teste, d.y_teste, melhor.prob_teste, limiar_linhas),
        },
        "calibracao": av.calibracao(d.y_teste, melhor.prob_teste),
        "importancia_shap": None,
    }
    if com_shap:
        try:
            inicio = time.time()
            extras["importancia_shap"] = av.importancia_shap(melhor.pipeline, d.X_teste)
            print(f"SHAP calculado em {time.time() - inicio:.0f}s")
        except ImportError:
            print("shap não instalado: importância das variáveis não calculada (pip install -r requirements-dev.txt).")
    return extras


def montar_metadados(
    escolhido: str,
    d: Divisao,
    total: int,
    treinados: dict[str, ModeloTreinado],
    vies: dict,
    testes: dict | None,
    extras: dict | None = None,
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
        "usa_cor_raca_e_sexo": True,
        "limiar_decisao": round(melhor.limiar, 4),
        "referencia": perfil_referencia(d.X_ajuste),
        "resultados": {nome: t.resultado for nome, t in treinados.items()},
        "analise_vies": vies,
        "testes_iniciais": testes,
        "curvas_roc": {nome: curva_roc(d.y_teste, t.prob_teste) for nome, t in treinados.items()},
        **(extras or {}),
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
        default="Nordeste",
        help="Região dos testes iniciais: compara o treino com e sem ela, avaliando nos alunos dela.",
    )
    parser.add_argument(
        "--modelo-testes", choices=list(MODELOS), default="mlp", help="Modelo usado nos testes iniciais."
    )
    parser.add_argument("--sem-testes", action="store_true", help="Pula os testes iniciais.")
    parser.add_argument("--sem-shap", action="store_true", help="Pula o cálculo do SHAP (mais rápido).")
    parser.add_argument(
        "--graficos", type=Path, default=Path("docs/resultados"), help="Pasta dos gráficos (precisa do matplotlib)."
    )
    return parser.parse_args()


def main() -> None:
    args = ler_argumentos()
    X, media, vies = preparar(args.amostra)
    print(f"Amostra: {len(X):,} alunos".replace(",", "."))

    divisao = dividir(X, media)
    print(f"Corte do quartil inferior (treino): média < {divisao.corte:.1f}")

    testes = None if args.sem_testes else testes_iniciais(divisao, vies, args.modelo_testes, args.teste_regiao)

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

    extras = avaliacoes_extras(divisao, vies, melhor, com_shap=not args.sem_shap) if not vies.empty else None
    metadados = montar_metadados(escolhido, divisao, len(X), treinados, vies_resultado, testes, extras)
    salvar_resultados(args.saida, melhor.pipeline, metadados)
    print(f"Salvo em {args.saida}/pipeline.pkl, metadados.json e relatorio_treino.md")

    # Risco de cada aluno da amostra para o painel do município (a API só lê o arquivo).
    risco = args.amostra.with_name("risco_municipios.parquet")
    if args.amostra.suffix == ".parquet" and args.saida == Path("models"):
        from .risco_municipios import gerar as gerar_risco

        print(f"Risco por aluno salvo em {gerar_risco(args.saida, args.amostra, risco)}")

    try:
        from .graficos import gerar_graficos
    except ImportError:
        print("matplotlib não instalado: gráficos não gerados (pip install -r requirements-dev.txt).")
    else:
        arquivos = gerar_graficos(metadados, args.graficos)
        print(f"{len(arquivos)} gráficos salvos em {args.graficos}/")


def _milhar(numero: int) -> str:
    return f"{numero:,}".replace(",", ".")


def _linha_tabela(*celulas) -> str:
    return "| " + " | ".join(str(c) for c in celulas) + " |"


def _pct(valor: float | None) -> str:
    return "-" if valor is None else f"{valor:.1%}"


def _relatorio_testes(t: dict | None) -> list[str]:
    if not t:
        return []
    r = t["regiao"]
    linhas = [
        f"## Testes iniciais ({t['modelo']}, mesmo conjunto de teste)",
        "",
        f"### Treino com e sem o {r['regiao']}",
        "",
        f"Avaliação nos {_milhar(r['n_teste_regiao'])} alunos do {r['regiao']} no conjunto de teste.",
        "",
        _linha_tabela(
            "Treino", "Alunos no treino", "AUC", "F1", "Recall", "Falso positivo", "Risco real", "Risco previsto"
        ),
        _linha_tabela(*["---"] * 8),
    ]
    for chave, rotulo, n in [
        ("com_regiao", f"Com o {r['regiao']}", r["n_treino_com"]),
        ("sem_regiao", f"Sem o {r['regiao']}", r["n_treino_sem"]),
    ]:
        v = r[chave]["na_regiao"]
        linhas.append(
            _linha_tabela(
                rotulo,
                _milhar(n),
                v["auc"],
                v["f1"],
                _pct(v["recall"]),
                _pct(v["falso_positivo"]),
                _pct(v["taxa_real_risco"]),
                _pct(v["risco_medio_previsto"]),
            )
        )
    cs = t["cor_sexo"]
    linhas += [
        "",
        "### Com e sem cor/raça e sexo",
        "",
        _linha_tabela("Modelo", "AUC", "F1", "Recall", "Falso positivo"),
        _linha_tabela(*["---"] * 5),
    ]
    for chave, rotulo in [("com", "Com cor/raça e sexo"), ("sem", "Sem cor/raça e sexo")]:
        v = cs[chave]["teste"]
        linhas.append(_linha_tabela(rotulo, v["auc"], v["f1"], _pct(v["recall"]), _pct(v["falso_positivo"])))
    linhas += ["", "Falso positivo por cor/raça (com → sem):", ""]
    com, sem = cs["com"]["vies"].get("cor_raca", {}), cs["sem"]["vies"].get("cor_raca", {})
    for g in com:
        if g in sem:
            linhas.append(
                f"- {c.COR_RACA.get(g, g)}: {_pct(com[g]['falso_positivo'])} → {_pct(sem[g]['falso_positivo'])}"
            )
    return [*linhas, ""]


def _relatorio_extras(m: dict) -> list[str]:
    linhas: list[str] = []
    regioes = (m.get("testes_iniciais") or {}).get("todas_regioes")
    if regioes:
        linhas += [
            "## Treino com e sem cada região",
            "",
            _linha_tabela(
                "Região", "Alunos no teste", "AUC com", "AUC sem", "Risco real", "Previsto com", "Previsto sem"
            ),
            _linha_tabela(*["---"] * 7),
        ]
        for reg, v in regioes.items():
            linhas.append(
                _linha_tabela(
                    reg,
                    _milhar(v["n_teste"]),
                    v["auc_com"],
                    v["auc_sem"],
                    _pct(v["risco_real"]),
                    _pct(v["previsto_com"]),
                    _pct(v["previsto_sem"]),
                )
            )
        linhas.append("")
    eq = m.get("equidade")
    if eq:
        antes, depois = m["analise_vies"].get("cor_raca", {}), eq["vies"].get("cor_raca", {})
        linhas += [
            "## Equidade: limiar por cor/raça",
            "",
            f"Critério: {eq['criterio']}. Limiar geral: {eq['limiar_geral']}.",
            "",
            _linha_tabela(
                "Grupo", "Limiar", "Recall antes", "Recall depois", "Falso positivo antes", "Falso positivo depois"
            ),
            _linha_tabela(*["---"] * 6),
        ]
        for g, v in depois.items():
            a = antes.get(g, {})
            linhas.append(
                _linha_tabela(
                    c.COR_RACA.get(g, g),
                    eq["limiares_cor_raca"].get(g, eq["limiar_geral"]),
                    _pct(a.get("recall")),
                    _pct(v["recall"]),
                    _pct(a.get("falso_positivo")),
                    _pct(v["falso_positivo"]),
                )
            )
        t = eq["teste"]
        linhas += ["", f"Geral com os limiares por grupo: F1 {t['f1']} · recall {_pct(t['recall'])}.", ""]
    cal = m.get("calibracao")
    if cal:
        linhas += [
            "## Calibração",
            "",
            f"Brier {cal['brier']} · diferença média entre o risco previsto e o real: {_pct(cal['erro_medio'])}.",
            "",
        ]
    imp = m.get("importancia_shap")
    if imp:
        linhas += [
            f"## Importância das variáveis (SHAP, {imp['alunos']} alunos do teste)",
            "",
            _linha_tabela("Variável", "Efeito médio (p.p.)"),
            _linha_tabela("---", "---"),
            *[_linha_tabela(k, v) for k, v in imp["pontos_percentuais"].items()],
            "",
        ]
    return linhas


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
        "- Entradas: questionário socioeconômico, escola, faixa etária, cor/raça e sexo (sem nenhuma nota)",
        "",
        *_relatorio_testes(m.get("testes_iniciais")),
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
    linhas += ["", *_relatorio_extras(m)]
    if m.get("analise_vies"):
        linhas += ["", "## Análise de viés (modelo escolhido, teste)", ""]
        for coluna, grupos in m["analise_vies"].items():
            linhas += [
                f"**{coluna}**",
                "",
                _linha_tabela("Grupo", "n", "Risco real", "Risco previsto", "Recall", "Falso positivo"),
                _linha_tabela(*["---"] * 6),
            ]
            rotulos = {"cor_raca": c.COR_RACA, "sexo": c.SEXO}.get(coluna, {})
            for g, v in grupos.items():
                linhas.append(
                    _linha_tabela(
                        rotulos.get(g, g),
                        v["n"],
                        f"{v['taxa_real_risco']:.1%}",
                        f"{v['taxa_prevista_risco']:.1%}",
                        f"{v['recall']:.1%}",
                        "-" if v["falso_positivo"] is None else f"{v['falso_positivo']:.1%}",
                    )
                )
            linhas.append("")
        linhas += [
            "Recall: dos alunos realmente no quartil inferior, quantos o modelo apontou.",
            "Falso positivo: dos alunos fora do quartil inferior, quantos o modelo apontou por engano.",
            "Cor/raça e sexo são entradas do modelo: veja nos testes iniciais o efeito de tirá-las.",
        ]
    return "\n".join(linhas) + "\n"


if __name__ == "__main__":
    main()
