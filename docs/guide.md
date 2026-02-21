# Usage Guide

Detailed reference for working with a bootstrapped project. For initial setup, see the [README](../readme.md).

## Running the Training Pipeline

```bash
# Run the full pipeline: preprocess → train → evaluate
dvc repro

# Or run individual stages
dvc repro -s preprocess
dvc repro -s train
dvc repro -s evaluate
```

## Viewing Training Logs

TensorBoard logs are stored locally in the `logs/` directory:

```bash
tensorboard --logdir logs
```

Then open http://localhost:6006 in your browser.

## Model Release Pipeline

To release a model (export to ONNX, create git tag, upload to S3):

```bash
# Run the full release pipeline
dvc repro -f dvc-release.yaml

# Or run individual stages
poetry run python -m {module_name}.scripts.release export-onnx
poetry run python -m {module_name}.scripts.release create-tag
poetry run python -m {module_name}.scripts.release upload-s3
```

## Model Versioning

Models are versioned using git tags:

```bash
# Tag a model version
poetry run python -m {module_name}.scripts.register_model --tag production-candidate
```

This creates a git tag like `model-production-candidate-{commit_hash}`.

---

## Configuration

### S3 Storage

The template is configured to use S3 for:

- **DVC data storage**: `s3://ml-data/dvcstore/{project_name}/`
- **Model releases**: `s3://ml-data/models/{project_name}/{version}/`

Configure these in `.dvc/config` and via environment variables (see `.env.example`).

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Key variables:
- `MODEL_RELEASE_S3_BUCKET`: S3 bucket for model releases (default: `ml-data`)
- `MODEL_RELEASE_S3_PREFIX`: S3 prefix for models (default: `models`)

### DVC Parameters

Edit `params.yaml` to configure:
- Data preprocessing parameters
- Training hyperparameters
- Evaluation settings
- Release configuration

### GPU Memory

If you hit out-of-memory (OOM) errors during training, try these in order:

1. **Reduce `batch_size`** in `params.yaml` (e.g. 32 -> 16 -> 8 -> 4)
2. **Reduce `image_size`** (e.g. `[224, 224]` -> `[128, 128]`)
3. **Use mixed precision**: add `precision="16-mixed"` to `create_trainer()` in `utils.py`

Large architectures (detection models, large backbones) may require `batch_size: 2-4` even on high-end GPUs.

---

## Dependencies

Core dependencies (installed by default with `poetry install`):

- `lightning` - Training framework (from Lightning AI)
- `torch`, `torchvision` - PyTorch (2.7.1, CUDA 12.8 wheels)
- `torchmetrics` - Metrics computation
- `tensorboard` - Experiment tracking (local)
- `dvc[s3]` - Data version control with S3 support
- `boto3` - AWS SDK
- `gitpython` - Git operations

Optional dependency groups:

| Group | Install command | Packages |
|-------|----------------|----------|
| `export` | `poetry install --with export` | `onnx`, `onnxruntime` |
| `cv` | `poetry install --with cv` | `timm`, `albumentations`, `pycocotools` |

Need a package not listed above? Add it directly:
```bash
poetry add <package>
```

See `pyproject.toml` for the complete list.

### Managing Dependencies

After bootstrap, you can manage dependencies using Poetry:

1. **Add a dependency**:
   ```bash
   poetry add package-name
   # For development dependencies:
   poetry add --group dev package-name
   ```

2. **Remove a dependency**:
   ```bash
   poetry remove package-name
   ```

3. **Update dependencies**:
   ```bash
   poetry update  # Update all dependencies
   poetry update package-name  # Update specific package
   ```

4. **Edit `pyproject.toml` directly** (Poetry will sync on next install):
   ```bash
   # Edit pyproject.toml, then run:
   poetry lock  # Update poetry.lock
   poetry install  # Install changes
   ```

5. **Export to requirements.txt** (if needed for other tools):
   ```bash
   poetry export -f requirements.txt --output requirements.txt --without-hashes
   ```

### PyTorch and CUDA Configuration

The template is configured with:
- **PyTorch version**: `2.7.1` (pinned)
- **PyTorch source**: `https://download.pytorch.org/whl/cu128` (CUDA 12.8)
- **Source priority**: `explicit` (only `torch` and `torchvision` use this source)

The PyTorch source is configured with `explicit` priority, meaning only `torch` and `torchvision` packages will be fetched from it. All other packages (like `dvc`, `boto3`, etc.) are fetched from PyPI, avoiding unnecessary authorization errors.

If you need a different CUDA version, you can update the PyTorch source URL in `pyproject.toml`:

```toml
[[tool.poetry.source]]
name = "pytorch"
url = "https://download.pytorch.org/whl/cu{version}"  # e.g., cu124, cu121, cu118
priority = "explicit"
```

The `torch` and `torchvision` dependencies are already configured to use this source:
```toml
[tool.poetry.dependencies]
torch = {version = "2.7.1", source = "pytorch"}
torchvision = {version = "0.22.1", source = "pytorch"}
```

Available CUDA versions can be found at: https://download.pytorch.org/whl/

After updating the source URL, run:
```bash
poetry lock
poetry install
```

---

## CI/CD

The template includes CircleCI configuration (`.circleci/config.yml`) for:

- Running tests
- Training and model registration
- Docker image building and pushing
- AWS Batch job submission

Configure CircleCI environment variables in your project settings.

---

## Docker

Build and run the training container using the provided build script:

```bash
# Uses Poetry to export requirements.txt, builds the image, cleans up
./docker_build.sh
docker run my-ml-project
```

Or build manually:
```bash
poetry export -f requirements.txt --output requirements.txt --without-hashes
docker build -t my-ml-project .
rm requirements.txt
```

The Dockerfile uses a multi-stage build with CUDA support for GPU training. It installs dependencies via `pip` from an exported `requirements.txt` (no Poetry in the image).
