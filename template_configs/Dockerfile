# Stage 1: Install dependencies
FROM nvidia/cuda:12.8.0-devel-ubuntu22.04 AS builder

ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-pip python3-venv && \
    rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM nvidia/cuda:12.8.0-runtime-ubuntu22.04

ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends python3 && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY src/${moduleName} /app/src/${moduleName}
COPY params.yaml ./

CMD ["python", "-m", "${moduleName}.train"]
