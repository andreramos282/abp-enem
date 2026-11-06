# EduPredict AI – imagem única com o front-end compilado e a API.
#
#   docker build -t edupredict .
#   docker run -p 8000:8000 edupredict
#   -> http://localhost:8000  (site)   |   http://localhost:8000/docs  (API)

# ---------- 1. Front-end ----------
FROM node:22-alpine AS front
WORKDIR /app/web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
# Token PÚBLICO do Mapbox, embutido no build do front (opcional: sem ele o mapa mostra um aviso).
ARG VITE_MAPBOX_ACCESS_TOKEN=""
ENV VITE_MAPBOX_ACCESS_TOKEN=${VITE_MAPBOX_ACCESS_TOKEN}
RUN npm run build

# ---------- 2. API + modelo ----------
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    MODO_PREDITOR=auto
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY api/ api/
COPY ml/ ml/
# Modelo treinado e amostra (se existirem). Sem eles, a API usa os dados simulados.
COPY models/ models/
COPY data/ data/
COPY --from=front /app/web/dist web/dist

RUN useradd --create-home app && chown -R app /app
USER app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:${PORT}/api/health')"
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT}"]
