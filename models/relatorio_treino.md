# Relatório de treino – gradient_boosting-20261105

- Dados: ENEM 2023 · 399.998 concluintes
- Divisão: ajuste 279.998 · validação 40.000 · teste 80.000
- Alvo: média das 5 notas no quartil inferior (média < 481.04)
- Modelo escolhido: **gradient_boosting**

## Comparação dos modelos (conjunto de teste)

| Modelo | AUC CV | AUC teste | F1 | Precisão | Recall | Limiar |
| --- | --- | --- | --- | --- | --- | --- |
| regressao_logistica | 0.7583 | 0.7551 | 0.518 | 0.4135 | 0.6934 | 0.2787 |
| arvore_decisao | 0.7478 | 0.7473 | 0.5126 | 0.3864 | 0.7612 | 0.2366 |
| random_forest | 0.7607 | 0.7598 | 0.5227 | 0.4109 | 0.7181 | 0.2674 |
| gradient_boosting | 0.7627 | 0.7619 | 0.5252 | 0.4185 | 0.705 | 0.2685 |
| mlp | 0.7574 | 0.7597 | 0.5206 | 0.4242 | 0.6738 | 0.2748 |

Teste sem a região **Nordeste** (88.036 alunos): AUC 0.7715

## Análise de viés (modelo escolhido, teste)

**cor_raca**

| Grupo | n | Risco real | Risco previsto | Recall | Falso positivo |
| --- | --- | --- | --- | --- | --- |
| Não declarado | 859 | 30.4% | 51.1% | 79.3% | 38.8% |
| Branca | 36613 | 16.4% | 26.3% | 55.2% | 20.6% |
| Preta | 8709 | 33.5% | 55.8% | 74.4% | 46.5% |
| Parda | 32183 | 31.6% | 55.1% | 77.6% | 44.7% |
| Amarela | 1188 | 27.2% | 44.6% | 78.0% | 32.1% |
| Indígena | 448 | 51.1% | 73.7% | 86.9% | 59.8% |

**sexo**

| Grupo | n | Risco real | Risco previsto | Recall | Falso positivo |
| --- | --- | --- | --- | --- | --- |
| Feminino | 47616 | 25.4% | 44.9% | 74.1% | 35.0% |
| Masculino | 32384 | 24.0% | 37.4% | 64.9% | 28.7% |

Recall: dos alunos realmente no quartil inferior, quantos o modelo apontou.
Falso positivo: dos alunos fora do quartil inferior, quantos o modelo apontou por engano.
Cor/raça e sexo NÃO são entradas do modelo; diferenças aqui vêm de variáveis associadas a elas.
