# Como contribuir

Guia rápido para o grupo trabalhar no mesmo repositório sem conflito.

## 1. Preparar o ambiente (uma vez)

```bash
git clone https://github.com/andreramos282/abp-enem.git
cd abp-enem

# Python (API e modelo)
python -m venv .venv
# Windows: .venv\Scripts\activate   |   Linux/Mac: source .venv/bin/activate
pip install -r requirements-dev.txt

# Front-end
cd web && npm install && cd ..

# Configuração local
cp .env.example .env   # no Windows: copy .env.example .env
```

No VS Code, aceite as extensões recomendadas (Ruff, ESLint, Prettier, Tailwind, EditorConfig). O código é formatado sozinho ao salvar.

## 2. Fluxo de trabalho

1. **Atualize a `main`** antes de começar:
   ```bash
   git checkout main
   git pull
   ```
2. **Crie uma branch** para a tarefa, com o prefixo do tipo de mudança:
   | Prefixo | Quando usar | Exemplo |
   |---|---|---|
   | `feat/` | nova funcionalidade | `feat/tela-relatorios` |
   | `fix/` | correção de erro | `fix/filtro-municipio` |
   | `ml/` | dados, EDA, treino | `ml/eda-renda` |
   | `docs/` | só documentação | `docs/relatorio-sprint-2` |
   | `chore/` | configuração, dependências | `chore/atualiza-vite` |

   ```bash
   git checkout -b feat/nome-da-tarefa
   ```
3. **Faça commits pequenos**, com mensagem no imperativo dizendo o que muda:
   - ✅ `Adiciona filtro por rede no painel`
   - ✅ `Corrige corte do quartil quando falta nota`
   - ❌ `ajustes`, `teste`, `versão final 2`
4. **Antes de enviar**, rode as verificações (as mesmas da CI):
   ```bash
   # Python
   ruff check . --fix && ruff format . && pytest

   # Front-end (dentro de web/)
   npm run lint && npm run format && npm test && npm run build
   ```
5. **Envie e abra um pull request** para a `main`:
   ```bash
   git push -u origin feat/nome-da-tarefa
   ```
   Preencha o modelo de descrição e peça revisão de **outra pessoa do grupo**.
6. **Merge só com a CI verde e uma aprovação.** Depois do merge, apague a branch.

## 3. Regras do código

- **Nomes em português**, claros e completos (`renda_per_capita`, não `rpc`).
- **Colunas do INEP** (`Q001`, `TP_ESCOLA`...) só aparecem em `ml/colunas_2023.py`. No resto do código, use os nomes do projeto.
- **Tratamento das variáveis** só em `ml/features.py`: ele é usado igual no treino e na API.
- **Contrato da API** em `docs/api.md`. Mudou o formato de entrada ou saída? Atualize o documento, os schemas (`api/schemas.py`) e os tipos do front (`web/src/lib/api.ts`) no mesmo pull request.
- **Textos da interface** em `web/src/lib/i18n.ts`, sempre em português **e** inglês (há um teste que confere).
- **Cores** pelos tokens de `web/src/index.css` (`bg-superficie`, `text-suave`...), nunca cores fixas. Assim o tema escuro continua funcionando.
- **Nada de dados ou modelos no git**: `.csv`, `.parquet` e `.pkl` ficam fora (já estão no `.gitignore`). Compartilhe pelo Drive.
- **Nada de segredos no git**: tokens ficam só no `.env`.
- **Testes**: mudou uma regra? Acrescente ou ajuste um teste em `tests/` (Python) ou `web/src/**/*.test.ts` (front).

## 4. Onde fica cada coisa

| Pasta | Conteúdo | Responsável principal |
|---|---|---|
| `ml/` | amostragem, variáveis, treino | Dados / Modelagem |
| `notebooks/` | EDA e experimentos | Análise |
| `api/` | API FastAPI | Back-end |
| `web/` | front-end React | Front-end |
| `docs/` | contrato da API e documentação | Todos |
| `tests/` | testes da API e do modelo | Todos |
