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
| Entradas | Escolaridade e ocupação dos pais, pessoas na casa, renda (e renda per capita), computador, internet, índice de bens, tipo/rede/localização da escola, região e faixa etária |
| Fora do modelo | **Notas** (só criam o alvo) · **cor/raça e sexo** (usados apenas na análise de viés) |
| Amostra | ~400 mil alunos, estratificada por região e tipo de escola, em Parquet, `random_state=42` |
| Validação | 80/20 estratificado + GridSearchCV (5 folds) no treino · teste extra deixando uma região de fora |
| Métricas | AUC (principal), F1 e recall da classe de risco |
| Modelos | Regressão Logística (baseline), Árvore de Decisão, Random Forest, Gradient Boosting (HistGradientBoosting, no lugar do XGBoost para evitar outra dependência) e MLP |

Fora do escopo atual: hábitos de estudo e evasão (não existem no questionário do ENEM). Possível extensão futura com os microdados do SAEB.

Todos os nomes de colunas do INEP ficam em [`ml/colunas_2023.py`](ml/colunas_2023.py). Para usar outro ano, crie um arquivo equivalente.

## Resultados com os dados reais (ENEM 2023)

Treino em 5 de novembro de 2026 com uma amostra estratificada de **399.998 concluintes**, tirada de 1.008.062 concluintes válidos.

| Modelo | AUC (teste) | F1 | Recall |
| --- | --- | --- | --- |
| Regressão logística (baseline) | 0,755 | 0,518 | 69% |
| Árvore de decisão | 0,747 | 0,513 | 76% |
| Random forest | 0,760 | 0,523 | 72% |
| Gradient boosting | 0,762 | 0,525 | 71% |
| **Rede neural (MLP)** (escolhida) | **0,760** | 0,521 | 67% |

- **Modelo escolhido: rede neural (MLP)**, camadas de 64 e 32 neurônios, como previsto no relatório da Sprint 1. A diferença para o melhor modelo (gradient boosting) é de só 0,002 de AUC.
- **Corte do quartil inferior:** média das 5 notas abaixo de **481,0**.
- **Teste sem a região Nordeste:** AUC 0,772. O modelo generaliza para uma região que não viu no treino.
- **Análise de viés:** mesmo sem cor/raça e sexo como entrada, o modelo aponta mais falsos positivos entre alunos pretos (43%) e pardos (42%) do que entre brancos (19%), e encontra menos alunos brancos que estão de fato em risco (recall de 52% contra 72–74%). Isso acompanha as diferenças reais de desempenho (risco real de 16% entre brancos e 32–34% entre pretos e pardos), mas é uma limitação a declarar: o resultado deve apoiar a decisão pedagógica, nunca rotular o aluno.

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
   python -m ml.treinar --teste-regiao Nordeste
   # para salvar a rede neural mesmo que outro modelo tenha AUC maior:
   python -m ml.treinar --escolher mlp
   ```
4. O resultado fica em `models/`: `pipeline.pkl` (modelo), `metadados.json` (corte, métricas, análise de viés) e `relatorio_treino.md` (tabelas prontas para o relatório da sprint).
5. Reinicie a API: ela passa a usar o modelo treinado automaticamente.

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
- [x] Treino com os dados reais (AUC 0,76)
- [x] Modelo final: rede neural (MLP)
- [x] Modelo (`models/pipeline.pkl`) e amostra (`data/amostra_enem_2023.parquet`) versionados no repositório
- [x] Imagem Docker com site + API + modelo
- [ ] Publicar (ver `docs/deploy.md`)
- [x] Integração do modelo real na API (com explicação dos fatores)
- [ ] Análise de viés e explicabilidade
