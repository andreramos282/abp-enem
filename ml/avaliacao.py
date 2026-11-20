"""Avaliações extras do modelo escolhido (usadas por ml/treinar.py).

- Equidade: um limiar de decisão por grupo de cor/raça, escolhido na validação para que todos
  os grupos tenham o mesmo recall (igualdade de oportunidade, Hardt et al., 2016).
- Calibração: se a probabilidade prevista corresponde à frequência real de alunos em risco.
- Importância das variáveis com SHAP (precisa do pacote shap, em requirements-dev.txt).
- Treino com e sem cada região, avaliando nos alunos da região.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss, recall_score, roc_auc_score
from sklearn.pipeline import Pipeline

from . import colunas_2023 as c

MINIMO_GRUPO = 100  # grupos menores que isso na validação usam o limiar geral


# --------------------------------------------------------------------------- equidade
def limiar_para_recall(y: np.ndarray, prob: np.ndarray, recall_alvo: float) -> float:
    """Maior limiar que ainda alcança o recall pedido (ou seja, o que gera menos alarmes)."""
    positivos = np.sort(prob[y == 1])[::-1]
    if len(positivos) == 0:
        return 0.5
    k = max(1, int(np.ceil(recall_alvo * len(positivos))))
    return float(positivos[k - 1])


def limiares_equidade(
    y: np.ndarray, prob: np.ndarray, grupos: pd.Series, limiar_geral: float, minimo: int = MINIMO_GRUPO
) -> dict[str, float]:
    """Um limiar por grupo, todos com o mesmo recall que o limiar geral tem na validação."""
    recall_alvo = recall_score(y, prob >= limiar_geral)
    grupos = grupos.astype(str).to_numpy()
    limiares = {}
    for grupo in np.unique(grupos):
        mascara = grupos == grupo
        if mascara.sum() < minimo or y[mascara].sum() == 0:
            continue
        limiares[grupo] = round(limiar_para_recall(y[mascara], prob[mascara], recall_alvo), 4)
    return limiares


def limiar_por_linha(grupos: pd.Series, limiares: dict[str, float], limiar_geral: float) -> np.ndarray:
    return grupos.astype(str).map(limiares).fillna(limiar_geral).to_numpy(dtype=float)


# --------------------------------------------------------------------------- calibração
def calibracao(y: np.ndarray, prob: np.ndarray, faixas: int = 10) -> dict:
    real, previsto = calibration_curve(y, prob, n_bins=faixas, strategy="quantile")
    return {
        "brier": round(float(brier_score_loss(y, prob)), 4),
        "erro_medio": round(float(np.mean(np.abs(real - previsto))), 4),
        "previsto": previsto.round(4).tolist(),
        "real": real.round(4).tolist(),
    }


# --------------------------------------------------------------------------- SHAP
# Variáveis do modelo agrupadas como aparecem para o usuário.
GRUPOS_SHAP = {
    "Renda per capita": ["renda_familiar", "pessoas_residencia", "renda_per_capita_log"],
    "Escolaridade da mãe": ["escolaridade_mae"],
    "Escolaridade do pai": ["escolaridade_pai"],
    "Ocupação da mãe": ["ocupacao_mae"],
    "Ocupação do pai": ["ocupacao_pai"],
    "Computador": ["computador"],
    "Internet": ["internet"],
    "Bens da casa": ["indice_bens"],
    "Rede da escola": ["rede_escola", "tipo_escola"],
    "Localização da escola": ["localizacao_escola"],
    "Região": ["regiao"],
    "Faixa etária": ["faixa_etaria"],
    "Cor/raça": ["cor_raca"],
    "Sexo": ["sexo"],
}


def _grupo_da_coluna(nome: str) -> str:
    base = nome.removeprefix("missingindicator_")
    for grupo, colunas in GRUPOS_SHAP.items():
        if any(base == col or base.startswith(f"{col}_") for col in colunas):
            return grupo
    return "Outros"


def importancia_shap(pipeline: Pipeline, X: pd.DataFrame, n: int = 400, fundo: int = 100, semente: int = 42) -> dict:
    """Média do |SHAP| por grupo de variáveis (em pontos percentuais de probabilidade).

    O SHAP é calculado nas colunas já tratadas (depois do one-hot) e somado por grupo.
    """
    import shap

    preparo, modelo = pipeline[:-1], pipeline[-1]
    rng = np.random.default_rng(semente)
    linhas = rng.choice(len(X), size=min(n + fundo, len(X)), replace=False)
    Z = preparo.transform(X.iloc[linhas])
    nomes = list(preparo[-1].get_feature_names_out())

    explicador = shap.PermutationExplainer(
        lambda z: modelo.predict_proba(z)[:, 1], shap.maskers.Independent(Z[:fundo], max_samples=fundo), seed=semente
    )
    valores = explicador(Z[fundo:], silent=True).values  # linhas x colunas

    por_grupo = pd.DataFrame(valores, columns=nomes).T.groupby(_grupo_da_coluna).sum().T
    media = por_grupo.abs().mean().sort_values(ascending=False) * 100
    return {"alunos": int(len(valores)), "pontos_percentuais": media.round(2).to_dict()}


# --------------------------------------------------------------------------- regiões
def regiao_de(X: pd.DataFrame) -> np.ndarray:
    return X["uf_escola"].astype("string").str.upper().map(c.REGIAO_POR_UF).fillna("NI").to_numpy()


def com_e_sem_cada_regiao(d, ajustar) -> dict:
    """Para cada região: AUC nos alunos dela com o modelo treinado com todo o Brasil e sem ela.

    d: Divisao (ml/treinar.py); ajustar(X, y) devolve um pipeline treinado.
    """
    reg_aj, reg_te = regiao_de(d.X_ajuste), regiao_de(d.X_teste)
    completo = ajustar(d.X_ajuste, d.y_ajuste)
    prob_completo = completo.predict_proba(d.X_teste)[:, 1]
    resultado = {}
    for regiao in ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]:
        teste = reg_te == regiao
        if len(np.unique(d.y_teste[teste])) < 2:
            continue  # região sem alunos (ou sem as duas classes) no teste
        sem = ajustar(d.X_ajuste[reg_aj != regiao], d.y_ajuste[reg_aj != regiao])
        prob_sem = sem.predict_proba(d.X_teste[teste])[:, 1]
        y = d.y_teste[teste]
        resultado[regiao] = {
            "n_teste": int(teste.sum()),
            "auc_com": round(float(roc_auc_score(y, prob_completo[teste])), 4),
            "auc_sem": round(float(roc_auc_score(y, prob_sem)), 4),
            "risco_real": round(float(y.mean()), 4),
            "previsto_com": round(float(prob_completo[teste].mean()), 4),
            "previsto_sem": round(float(prob_sem.mean()), 4),
        }
    return resultado
