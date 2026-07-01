# ── Stage 1: train (optional — run locally or in CI) ──────────────────────
FROM python:3.11-slim AS trainer

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MLFLOW_TRACKING_URI=http://mlflow:5000

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY monitoring/ monitoring/

# Default: no-op; override with `docker build --target trainer` + run command
CMD ["python", "-m", "src.train"]

# ── Stage 2: slim API image ────────────────────────────────────────────────
FROM python:3.11-slim AS api

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MODEL_PATH=/app/models/wine_quality_model.pkl \
    MODEL_METADATA_PATH=/app/models/model_metadata.json

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir \
    fastapi uvicorn[standard] pydantic joblib numpy scikit-learn xgboost python-dotenv

COPY src/ src/
COPY models/ models/

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

CMD ["uvicorn", "src.serve.main:app", "--host", "0.0.0.0", "--port", "8000"]
