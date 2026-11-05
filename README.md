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
| Modelos | Regressão Logística (baseline), Árvore de Decisão, Random Forest, XGBoost e MLP |

Fora do escopo atual: hábitos de estudo e evasão (não existem no questionário do ENEM). Possível extensão futura com os microdados do SAEB.

Todos os nomes de colunas do INEP ficam em [`ml/colunas_2023.py`](ml/colunas_2023.py). Para usar outro ano, crie um arquivo equivalente.

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

## Como rodar a API

Requer Python 3.11+.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   |   Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
```

Acesse `http://127.0.0.1:8000/docs` para testar os endpoints no navegador.

Enquanto o modelo não estiver pronto, a API responde com **dados simulados** (`USAR_MOCK=true`), no formato definitivo. Os valores do mock não são resultados do projeto.

## Como rodar o front-end

Requer Node.js 20+.

```bash
cd web
npm install
npm run dev   # sobe o front (http://localhost:5173) e a API juntos
```

Para exibir o mapa, copie `.env.example` para `.env` na raiz e coloque seu token público do Mapbox. Detalhes em [`web/README.md`](web/README.md).

### Testes

```bash
pytest
```

Os testes também rodam automaticamente a cada pull request (GitHub Actions).

## Como contribuir

1. Crie uma branch a partir da `main`: `git checkout -b feat/nome-da-tarefa`
2. Faça commits pequenos e com mensagens claras.
3. Abra um pull request e peça revisão de outra pessoa do grupo.
4. Só faça merge com os testes passando.

## Roadmap

- [x] Estrutura do repositório e contrato da API
- [x] API com respostas simuladas (mock)
- [x] Front-end responsivo consumindo a API (mapa, "Nova análise" e resultado)
- [ ] Amostra limpa do ENEM 2023 e EDA
- [ ] Modelos baseline e modelo final
- [ ] Integração do modelo real na API
- [ ] Análise de viés e explicabilidade
