# Relatório de treino – mlp-20261119

- Dados: ENEM 2023 · 399.998 concluintes
- Divisão: ajuste 279.998 · validação 40.000 · teste 80.000
- Alvo: média das 5 notas no quartil inferior (média < 481.04)
- Modelo escolhido: **mlp**
- Entradas: questionário socioeconômico, escola, faixa etária, cor/raça e sexo (sem nenhuma nota)

## Testes iniciais (mlp, mesmo conjunto de teste)

### Treino com e sem o Nordeste

Avaliação nos 17.607 alunos do Nordeste no conjunto de teste.

| Treino | Alunos no treino | AUC | F1 | Recall | Falso positivo | Risco real | Risco previsto |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Com o Nordeste | 279.998 | 0.7734 | 0.5753 | 82.9% | 43.1% | 29.0% | 30.0% |
| Sem o Nordeste | 218.372 | 0.768 | 0.556 | 91.9% | 56.8% | 29.0% | 32.3% |

### Com e sem cor/raça e sexo

| Modelo | AUC | F1 | Recall | Falso positivo |
| --- | --- | --- | --- | --- |
| Com cor/raça e sexo | 0.7634 | 0.5241 | 72.1% | 34.2% |
| Sem cor/raça e sexo | 0.7597 | 0.5206 | 67.4% | 30.3% |

Falso positivo por cor/raça (com → sem):

- Não declarado: 44.3% → 37.0%
- Branca: 16.5% → 19.1%
- Preta: 57.9% → 42.6%
- Parda: 51.3% → 42.1%
- Amarela: 41.3% → 29.7%
- Indígena: 84.9% → 54.8%

## Comparação dos modelos (conjunto de teste)

| Modelo | AUC CV | AUC teste | F1 | Precisão | Recall | Limiar |
| --- | --- | --- | --- | --- | --- | --- |
| regressao_logistica | 0.7609 | 0.7585 | 0.5225 | 0.4079 | 0.7265 | 0.2644 |
| arvore_decisao | 0.7515 | 0.7543 | 0.5182 | 0.4042 | 0.722 | 0.2614 |
| random_forest | 0.7641 | 0.7627 | 0.5258 | 0.4146 | 0.7187 | 0.2689 |
| gradient_boosting | 0.7668 | 0.765 | 0.5288 | 0.4253 | 0.6989 | 0.2744 |
| mlp | 0.7635 | 0.7631 | 0.5251 | 0.4267 | 0.6824 | 0.2647 |

## Análise de viés (modelo escolhido, teste)

**cor_raca**

| Grupo | n | Risco real | Risco previsto | Recall | Falso positivo |
| --- | --- | --- | --- | --- | --- |
| Não declarado | 859 | 30.4% | 54.9% | 83.9% | 42.3% |
| Branca | 36613 | 16.4% | 18.0% | 41.8% | 13.3% |
| Preta | 8709 | 33.5% | 63.0% | 81.2% | 53.8% |
| Parda | 32183 | 31.6% | 56.7% | 78.6% | 46.6% |
| Amarela | 1188 | 27.2% | 52.1% | 85.1% | 39.8% |
| Indígena | 448 | 51.1% | 90.0% | 97.4% | 82.2% |

**sexo**

| Grupo | n | Risco real | Risco previsto | Recall | Falso positivo |
| --- | --- | --- | --- | --- | --- |
| Feminino | 47616 | 25.4% | 41.6% | 70.6% | 31.8% |
| Masculino | 32384 | 24.0% | 37.0% | 64.6% | 28.3% |

Recall: dos alunos realmente no quartil inferior, quantos o modelo apontou.
Falso positivo: dos alunos fora do quartil inferior, quantos o modelo apontou por engano.
Cor/raça e sexo são entradas do modelo: veja nos testes iniciais o efeito de tirá-las.
