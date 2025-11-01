# Stage 1: Build/Install Dependencies
FROM cuda/cuda:12.8.0-devel-ubuntu22.04 as builder 
# Set environment variables for Poetry and Python
ENV PYTHONUNBUFFERED=1
ENV POETRY_VIRTUALENVS_CREATE=false
ENV POETRY_CACHE_DIR="/tmp/poetry_cache"
WORKDIR /app

# Copy project metadata files
COPY pyproject.toml poetry.lock ./

# Install dependencies first (leverages cache layer)
RUN pip install poetry
# Use the specific groups required for training/runtime
RUN poetry install --no-dev --with s3_storage

# Stage 2: Final Runtime Image
FROM cuda/cuda:12.8.0-runtime-ubuntu22.04
# Set entrypoint to unbuffered python
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy only the necessary packages from the builder stage
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin/ /usr/local/bin/
# Copy application code and DVC files
COPY src/${moduleName} /app/${moduleName}
COPY dvc.yaml params.yaml .dvcignore ./

# Optional: Pull data in the remote training environment
# ENTRYPOINT [ "python" "-m" "dvc" "pull" ]
# CMD ["python", "-m", "my_ml_project.train"],
# Default command for training via DVC pipelines,
CMD ["python", "-m", "dvc", "repro"],