# Relatório de treino – mlp-20261106

- Dados: ENEM 2023 · 399.998 concluintes
- Divisão: ajuste 279.998 · validação 40.000 · teste 80.000
- Alvo: média das 5 notas no quartil inferior (média < 481.04)
- Modelo escolhido: **mlp**

## Comparação dos modelos (conjunto de teste)

| Modelo | AUC CV | AUC teste | F1 | Precisão | Recall | Limiar |
| --- | --- | --- | --- | --- | --- | --- |
| regressao_logistica | 0.7583 | 0.7551 | 0.518 | 0.4135 | 0.6934 | 0.2787 |
| arvore_decisao | 0.7478 | 0.7473 | 0.5126 | 0.3864 | 0.7612 | 0.2366 |
| random_forest | 0.7607 | 0.7598 | 0.5227 | 0.4109 | 0.7181 | 0.2674 |
| gradient_boosting | 0.7627 | 0.7619 | 0.5252 | 0.4185 | 0.705 | 0.2685 |
| mlp | 0.7574 | 0.7597 | 0.5206 | 0.4242 | 0.6738 | 0.2748 |

Teste sem a região **Nordeste** (88.036 alunos): AUC 0.7714

## Análise de viés (modelo escolhido, teste)

**cor_raca**

| Grupo | n | Risco real | Risco previsto | Recall | Falso positivo |
| --- | --- | --- | --- | --- | --- |
| Não declarado | 859 | 30.4% | 49.7% | 78.9% | 37.0% |
| Branca | 36613 | 16.4% | 24.5% | 52.1% | 19.1% |
| Preta | 8709 | 33.5% | 52.3% | 71.6% | 42.6% |
| Parda | 32183 | 31.6% | 52.3% | 74.2% | 42.1% |
| Amarela | 1188 | 27.2% | 42.2% | 75.5% | 29.7% |
| Indígena | 448 | 51.1% | 70.3% | 85.2% | 54.8% |

**sexo**

| Grupo | n | Risco real | Risco previsto | Recall | Falso positivo |
| --- | --- | --- | --- | --- | --- |
| Feminino | 47616 | 25.4% | 42.3% | 70.9% | 32.6% |
| Masculino | 32384 | 24.0% | 35.3% | 61.9% | 26.9% |

Recall: dos alunos realmente no quartil inferior, quantos o modelo apontou.
Falso positivo: dos alunos fora do quartil inferior, quantos o modelo apontou por engano.
Cor/raça e sexo NÃO são entradas do modelo; diferenças aqui vêm de variáveis associadas a elas.
