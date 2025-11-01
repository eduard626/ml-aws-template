# Stage 1: Build/Install Dependencies
FROM cuda/cuda:12.8.0-devel-ubuntu22.04 as builder 
# Set environment variables for Python
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Copy requirements and install dependencies first (leverages cache layer)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

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