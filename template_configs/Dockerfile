# Stage 1: Build/Install Dependencies
FROM cuda/cuda:12.8.0-devel-ubuntu22.04 as builder 
# Set environment variables for Python
ENV PYTHONUNBUFFERED=1
ENV POETRY_NO_INTERACTION=1
ENV POETRY_VENV_IN_PROJECT=1
ENV POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy Poetry files and install dependencies first (leverages cache layer)
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-dev --no-root && rm -rf $POETRY_CACHE_DIR

# Stage 2: Final Runtime Image
FROM cuda/cuda:12.8.0-runtime-ubuntu22.04
# Set entrypoint to unbuffered python
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy Poetry virtual environment from builder stage
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code and DVC files
COPY src/${moduleName} /app/${moduleName}
COPY dvc.yaml params.yaml .dvcignore ./

# Optional: Pull data in the remote training environment
# ENTRYPOINT [ "python" "-m" "dvc" "pull" ]
# CMD ["python", "-m", "my_ml_project.train"],
# Default command for training via DVC pipelines,
CMD ["python", "-m", "dvc", "repro"],