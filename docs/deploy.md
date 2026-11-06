# Como publicar o EduPredict AI

A aplicação inteira roda num único container: a API (FastAPI) entrega o site já compilado, o modelo (`models/pipeline.pkl`) e a amostra do ENEM 2023 (`data/amostra_enem_2023.parquet`).

## Rodar com Docker no próprio computador

Requer o [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```bash
docker compose up --build
```

- Site: http://localhost:8000
- Documentação da API: http://localhost:8000/docs

Para o mapa aparecer, coloque `VITE_MAPBOX_ACCESS_TOKEN=pk...` no `.env` da raiz antes de rodar o comando. O token é embutido no site durante o build.

## Publicar na internet (Render, plano gratuito)

1. Crie uma conta em https://render.com com o GitHub.
2. **New → Web Service** e escolha o repositório `abp-enem`.
3. Em **Language/Runtime**, escolha **Docker**. O Render usa o `Dockerfile` da raiz.
4. Em **Environment Variables**, adicione `VITE_MAPBOX_ACCESS_TOKEN` com o token público do Mapbox.
5. Em **Health Check Path**, use `/api/health`.
6. Clique em **Create Web Service**. O endereço fica parecido com `https://edupredict-ai.onrender.com`.

O Render recompila a cada push na `main`.

Observações do plano gratuito:
- O serviço "dorme" depois de um tempo sem acesso, e a primeira visita pode levar cerca de 1 minuto.
- Há 512 MB de memória. A amostra só é carregada na primeira busca de município.
- Se o mapa não aparecer, confira se o token foi passado no build. Em alguns provedores, a variável precisa estar marcada como disponível no build.

Outras opções com Docker que funcionam do mesmo jeito: Railway, Fly.io e Google Cloud Run.

## Atualizar o modelo

1. Treine de novo (`python -m ml.treinar ...`). O resultado vai para `models/`.
2. Faça commit de `models/pipeline.pkl`, `models/metadados.json` e `models/relatorio_treino.md`.
3. Depois do merge na `main`, o deploy usa o modelo novo.
