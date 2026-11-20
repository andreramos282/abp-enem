# EduPredict AI – Predição de risco de desempenho no ENEM

Projeto ABP do 5º semestre de DSM (FATEC Jacareí).

Plataforma de inteligência educacional para secretarias de educação e escolas públicas: estima o **risco de um aluno concluinte ficar no quartil inferior de desempenho no ENEM** a partir do perfil socioeconômico e escolar, e aponta perfis que precisam de intervenção pedagógica.

## Definição do problema

| Item | Decisão |
|---|---|
| Base de treino | Microdados do **ENEM 2023** (último ano com questionário e notas no mesmo arquivo) |
| Tipo | Classificação binária |
| População | Concluintes do ensino médio (`TP_ST_CONCLUSAO = 2`), presentes nas 4 provas e com redação válida |
| Alvo | `1` se a média das 5 notas estiver no **quartil inferior** (corte calculado só no treino) |
| Entradas | Escolaridade e ocupação dos pais, pessoas na casa, renda (e renda per capita), computador, internet, índice de bens, tipo/rede/localização da escola, região, faixa etária, **cor/raça e sexo** |
| Fora do modelo | **Notas** (só criam o alvo) |
| Amostra | ~400 mil alunos, estratificada por região e tipo de escola, em Parquet, `random_state=42` |
| Validação | 70/10/20 estratificado + GridSearchCV (5 folds) no treino · testes iniciais com e sem o Nordeste e com e sem cor/raça e sexo |
| Métricas | AUC (principal), F1 e recall da classe de risco |
| Modelos | Regressão Logística (baseline), Árvore de Decisão, Random Forest, Gradient Boosting (HistGradientBoosting, no lugar do XGBoost para evitar outra dependência) e MLP |

Fora do escopo atual: hábitos de estudo e evasão (não existem no questionário do ENEM). Possível extensão futura com os microdados do SAEB.

Todos os nomes de colunas do INEP ficam em [`ml/colunas_2023.py`](ml/colunas_2023.py). Para usar outro ano, crie um arquivo equivalente.

## Resultados com os dados reais (ENEM 2023)

Treino em 19 de novembro de 2026 com uma amostra estratificada de **399.998 concluintes**, tirada de 1.008.062 concluintes válidos. Gráficos em [`docs/resultados/`](docs/resultados/).

### Testes iniciais

Feitos antes da comparação dos modelos, com a mesma rede neural e o mesmo conjunto de teste.

**Treino com e sem o Nordeste**, avaliando nos 17.607 alunos do Nordeste do teste:

| Treino | AUC | Recall | Falso positivo | Risco real | Risco previsto (médio) |
| --- | --- | --- | --- | --- | --- |
| Com o Nordeste | 0,773 | 83% | 43% | 29,0% | 30,0% |
| Sem o Nordeste | 0,768 | 92% | 57% | 29,0% | 32,3% |

O modelo funciona numa região que nunca viu (AUC cai só 0,005), mas superestima o risco lá e aponta mais alunos por engano. Treinar com todas as regiões é melhor.

**Com e sem cor/raça e sexo:**

| Modelo | AUC | Falso positivo: brancos | pretos | pardos | indígenas |
| --- | --- | --- | --- | --- | --- |
| Com cor/raça e sexo (usado no site) | 0,763 | 17% | 58% | 51% | 85% |
| Sem cor/raça e sexo | 0,760 | 19% | 43% | 42% | 55% |

Cor/raça e sexo melhoram a AUC em só **0,004**, e o modelo passa a apontar por engano muito mais alunos pretos, pardos e indígenas que não estão em risco. Isso precisa ser declarado no relatório: são dados sensíveis (LGPD, art. 11) e o resultado deve apoiar a decisão pedagógica, nunca rotular o aluno.

**Treino com e sem cada região** (AUC nos alunos da região):

| Região | Com a região | Sem a região |
| --- | --- | --- |
| Norte | 0,765 | 0,762 |
| Nordeste | 0,773 | 0,768 |
| Centro-Oeste | 0,770 | 0,768 |
| Sudeste | 0,769 | 0,765 |
| Sul | 0,758 | 0,755 |

O modelo generaliza para qualquer região (perde no máximo 0,005 de AUC), mas erra o nível de risco de quem não viu: sem o Sudeste no treino, prevê 20% de alunos em risco lá, contra 15% reais.

### Equidade, calibração e explicabilidade

- **Limiar por cor/raça (equidade):** com um limiar único, o modelo encontrava 42% dos alunos brancos em risco e 81% dos pretos, e apontava por engano 13% dos brancos e 54% dos pretos. Com um limiar por grupo, escolhido na validação para que todos tenham o mesmo recall (igualdade de oportunidade), o recall fica entre 67% e 72% em todos os grupos e o falso positivo entre 28% e 39%. O site usa esses limiares no aviso de "acompanhamento recomendado".
- **Calibração:** o risco previsto bate com o real (diferença média de 1,1 ponto percentual, Brier 0,156). Quando o site mostra 30% de risco, cerca de 30% desses alunos estão de fato no quartil inferior. Não foi preciso recalibrar.
- **Importância das variáveis (SHAP):** as que mais pesam são renda per capita, rede da escola, faixa etária e computador em casa. Cor/raça vem em 5º lugar e sexo quase não pesa.

### Comparação dos modelos (com cor/raça e sexo)

| Modelo | AUC (teste) | F1 | Recall |
| --- | --- | --- | --- |
| Regressão logística (baseline) | 0,758 | 0,523 | 73% |
| Árvore de decisão | 0,754 | 0,518 | 72% |
| Random forest | 0,763 | 0,526 | 72% |
| Gradient boosting | 0,765 | 0,529 | 70% |
| **Rede neural (MLP)** (escolhida) | **0,763** | 0,525 | 68% |

- **Modelo escolhido: rede neural (MLP)**, camadas de 128 e 64 neurônios, como previsto no relatório da Sprint 1. A diferença para o melhor modelo (gradient boosting) é de 0,002 de AUC.
- **Corte do quartil inferior:** média das 5 notas abaixo de **481,0**.
- **Viés por sexo:** pequeno (falso positivo de 32% no feminino e 28% no masculino).

Detalhes em [`models/relatorio_treino.md`](models/relatorio_treino.md) e análise exploratória em [`docs/eda/`](docs/eda/README.md).

## Estrutura

```
api/        API FastAPI (contrato em docs/api.md)
ml/         Mapeamento de colunas, pipeline e treino do modelo
notebooks/  EDA e experimentos
models/     Modelo treinado (.pkl fica fora do git)
data/       Dados do ENEM (fora do git; ver data/README.md)
web/        Front-end (React + Vite + Mapbox)
docs/       Documentação
tests/      Testes automatizados
```

## Rodar tudo com Docker

```bash
docker compose up --build
```

O site fica em http://localhost:8000 e a API em http://localhost:8000/docs, já com o modelo treinado. Para publicar na internet, veja [`docs/deploy.md`](docs/deploy.md).

## Como rodar a API

Requer Python 3.11+.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   |   Linux/Mac: source .venv/bin/activate
pip install -r requirements-dev.txt   # só para rodar a API: requirements.txt
cp .env.example .env                  # no Windows: copy .env.example .env
uvicorn api.main:app --reload --port 8000
```

A API lê as configurações do arquivo `.env` da raiz (variáveis definidas no terminal têm prioridade).

Acesse `http://127.0.0.1:8000/docs` para testar os endpoints no navegador.

Se existir um modelo treinado em `models/pipeline.pkl`, a API usa o modelo. Senão, responde com **dados simulados** no formato definitivo (campo `"modelo": "mock"`), que não são resultados do projeto. Para forçar um dos dois, use `MODO_PREDITOR=mock` ou `MODO_PREDITOR=modelo` (ver `.env.example`).

## Como gerar a amostra e treinar o modelo

1. Baixe os microdados do ENEM 2023 e coloque o `MICRODADOS_ENEM_2023.csv` em `data/` (ver [`data/README.md`](data/README.md)).
2. Gere a amostra (lê o arquivo em blocos; leva alguns minutos):
   ```bash
   python -m ml.preparar_dados data/MICRODADOS_ENEM_2023.csv
   ```
3. Treine e compare os modelos:
   ```bash
   python -m ml.treinar   # testes iniciais com e sem o Nordeste (mude com --teste-regiao)
   # para salvar a rede neural mesmo que outro modelo tenha AUC maior:
   python -m ml.treinar --escolher mlp
   ```
4. O resultado fica em `models/`: `pipeline.pkl` (modelo), `metadados.json` (corte, métricas, testes iniciais, análise de viés) e `relatorio_treino.md` (tabelas prontas para o relatório da sprint). Os gráficos vão para `docs/resultados/` (refaça só os gráficos com `python -m ml.graficos`).
5. Reinicie a API: ela passa a usar o modelo treinado automaticamente.
6. (Opcional) Teste em outro ano: baixe os microdados do ENEM 2022 e rode
   `python -m ml.teste_temporal data/MICRODADOS_ENEM_2022.csv --ano 2022`. O resultado vai para
   `models/teste_temporal_2022.json` e o gráfico para `docs/resultados/`.

Para testar o fluxo sem os dados reais: `python -m tests.sintetico data/MICRODADOS_ENEM_2023_SINTETICO.csv` gera um arquivo falso no mesmo layout.

## Como rodar o front-end

Requer Node.js 20+.

```bash
cd web
npm install
npm run dev   # sobe o front (http://localhost:5173) e a API juntos
```

Para exibir o mapa, copie `.env.example` para `.env` na raiz e coloque seu token público do Mapbox. Detalhes em [`web/README.md`](web/README.md).

### Testes e verificação de estilo

```bash
# Python
pytest
ruff check . && ruff format --check .

# Front-end (dentro de web/)
npm test
npm run lint && npm run format:check
```

Tudo isso roda automaticamente a cada pull request (GitHub Actions).

## Como contribuir

Veja o [CONTRIBUTING.md](CONTRIBUTING.md): preparação do ambiente, padrão de branches e commits, verificações antes do pull request e regras do código.

## Roadmap

- [x] Estrutura do repositório e contrato da API
- [x] API com respostas simuladas (mock)
- [x] Front-end responsivo consumindo a API (mapa, "Nova análise" e resultado)
- [x] Script de amostragem do ENEM 2023
- [x] Amostragem com os microdados reais e EDA (`python -m ml.eda`)
- [x] Script de treino: baselines, MLP, GridSearchCV, limiar, viés e teste por região
- [x] Cor/raça e sexo no modelo, testes iniciais (com e sem Nordeste, com e sem cor/raça e sexo) e gráficos
- [x] Treino com os dados reais (AUC 0,76)
- [x] Modelo final: rede neural (MLP)
- [x] Modelo (`models/pipeline.pkl`) e amostra (`data/amostra_enem_2023.parquet`) versionados no repositório
- [x] Imagem Docker com site + API + modelo
- [ ] Publicar (ver `docs/deploy.md`)
- [x] Integração do modelo real na API (com explicação dos fatores)
- [x] Análise de viés e explicabilidade (limiar por cor/raça, calibração e SHAP)
- [x] Painel do município: comparação com estado e Brasil e risco por rede de ensino
- [x] Análise em lote (planilha CSV) e fatores separados em "ação" e "contexto"
- [ ] Teste no ENEM 2022 (script pronto: `ml/teste_temporal.py`; falta rodar com os microdados de 2022)
