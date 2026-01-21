# ---------- Stage 1: Build dependencies ----------
FROM python:3.12-slim AS builder

# Install system dependencies required for building some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    git \
 && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Install Poetry (optional, better dependency management)
RUN curl -sSL https://install.python-poetry.org | python3 -

# Copy dependency files
COPY pyproject.toml poetry.lock* /app/

# Install dependencies in isolated virtualenv
RUN poetry config virtualenvs.create true \
 && poetry install --no-root --no-dev

# ---------- Stage 2: Production image ----------
FROM python:3.12-slim

# Set workdir
WORKDIR /app

# Copy virtualenv from builder
COPY --from=builder /root/.cache/pypoetry /root/.cache/pypoetry
COPY --from=builder /app /app

# Set PATH for poetry virtualenv
ENV PATH="/root/.cache/pypoetry/virtualenvs/*/bin:$PATH"

# Copy application code
COPY . /app

# Expose port
EXPOSE 8000

# Run Uvicorn with Gunicorn for production
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "2", "--timeout", "60"]
