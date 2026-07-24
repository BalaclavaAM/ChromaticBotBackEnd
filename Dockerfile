# Stage 1: install production dependencies with PDM
FROM python:3.12-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir pdm

COPY pyproject.toml pdm.lock ./
RUN pdm install --check --prod --no-editable

# Stage 2: runtime
FROM python:3.12-slim

WORKDIR /app

RUN groupadd --system app && useradd --system --gid app app

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

COPY app ./app

USER app

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=3)"]

# 2 workers: acorde a contenedores de ~512MB; subir junto con la memoria
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
