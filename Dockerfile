# syntax=docker/dockerfile:1

# --- Base stage ---
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install system deps (for pypdf and transformers backends)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libglib2.0-0 \
        libgl1 \
        git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first (better layer caching)
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Optional: create a non-root user
RUN useradd -m appuser
USER appuser

# Copy project
COPY --chown=appuser:appuser app /app/app
COPY --chown=appuser:appuser README.md /app/README.md
COPY --chown=appuser:appuser Procfile /app/Procfile

# Expose port
EXPOSE 8000

# Healthcheck (simple)
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000').read()" || exit 1

# Hugging Face cache (optional)
ENV HF_HOME=/app/.hf_cache

# Start
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
