FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MLFLOW_DISABLE_AGENT_HINT=1 \
    MLFLOW_ENABLE_TELEMETRY=false

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir . \
    && useradd --create-home --uid 10001 appuser \
    && mkdir /workspace \
    && chown appuser:appuser /workspace

COPY params.yaml /app/params.yaml
COPY scripts/smoke_test.py /app/scripts/smoke_test.py
USER appuser
WORKDIR /workspace
ENTRYPOINT ["python", "-m", "house_price"]
CMD ["--help"]
