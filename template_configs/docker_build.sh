#!/usr/bin/env bash
set -euo pipefail

echo "Exporting requirements.txt from Poetry..."
poetry export -f requirements.txt --output requirements.txt --without-hashes

echo "Building Docker image: ${projectName}..."
docker build -t ${projectName} .

echo "Cleaning up requirements.txt..."
rm -f requirements.txt

echo "Done. Run with: docker run ${projectName}"
