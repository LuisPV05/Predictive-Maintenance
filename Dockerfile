FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# libgomp1 es necesaria para LightGBM
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

# Modelos y datos de ejemplo desde la Release de GitHub
ARG RELEASE_URL=https://github.com/LuisPV05/Predictive-Maintenance/releases/download/v0.1.0
RUN mkdir -p data/raw \
    && curl -fsSL -o models_lightgbm.joblib "$RELEASE_URL/models_lightgbm.joblib" \
    && curl -fsSL -o models_scaler.joblib "$RELEASE_URL/models_scaler.joblib" \
    && curl -fsSL -o data/raw/test_FD001.txt "$RELEASE_URL/test_FD001.txt"

COPY src ./src
COPY app ./app

EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]