# Modelos

Gerados por `python -m ml.treinar` (ver README principal). O modelo final fica versionado no git para o deploy:

| Arquivo | Conteúdo |
|---|---|
| `pipeline.pkl` | `Pipeline` do scikit-learn com engenharia de variáveis (`ml/features.py`), pré-processamento e classificador. É o que a API carrega. |
| `metadados.json` | Modelo escolhido, versão do scikit-learn, corte do quartil, limiar de decisão, perfil de referência, métricas de todos os modelos, análise de viés e teste por região. |
| `relatorio_treino.md` | Tabelas de comparação e de viés prontas para colar no relatório da sprint. |

Ao treinar um modelo novo, faça commit dos três arquivos.
A versão do scikit-learn de quem treina e de quem roda a API deve ser a mesma (`requirements.txt`).
