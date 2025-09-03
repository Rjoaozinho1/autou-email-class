# --- Base stage ---
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libglib2.0-0 \
        libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

RUN useradd -m appuser
USER appuser

# Debug-friendly defaults and cache location
ENV LOG_LEVEL=DEBUG
# HF_HOME=/home/appuser/.cache/huggingface \
# TRANSFORMERS_CACHE=/home/appuser/.cache/huggingface/transformers

COPY --chown=appuser:appuser app /app/app
COPY --chown=appuser:appuser Procfile /app/Procfile

EXPOSE 8000

# HEALTHCHECK --interval=30s --timeout=3s --start-period=20s \
#   CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000').read()" || exit 1

# Start
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
