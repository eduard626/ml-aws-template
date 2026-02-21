# ML AWS Template

A template for machine learning projects on AWS, using Lightning (from Lightning AI), DVC for data versioning, S3 for storage, and TensorBoard for experiment tracking.

## Features

- **Lightning** (from Lightning AI) for training and evaluation
- **DVC** for data versioning and pipeline management
- **S3** for model and data storage
- **TensorBoard** for local experiment tracking
- **ONNX** export for model deployment
- **Git-based** model versioning
- **Docker** support for containerized training
- **CI/CD** ready with CircleCI configuration

## Prerequisites

- **Python 3.10+**
- **Git**

## Quick Start

### 1. Create a new project directory

```bash
mkdir my-new-ml-project
cd my-new-ml-project
git init
```

### 2. Add this template as a submodule (hidden directory)

```bash
git submodule add https://github.com/eduard626/ml-aws-template.git .ml-aws-template
```

### 3. Run the bootstrap script (one-time setup)

```bash
python3 .ml-aws-template/bootstrap.py
```

**Note:** Bootstrap is intended to be run **only once** for initial scaffolding. After bootstrap, you can freely edit `pyproject.toml` and other files directly.

The bootstrap script will:
- ✅ Copy the template configuration to your project
- ✅ Generate project structure with Python source code
- ✅ Create DVC pipeline configurations (`dvc.yaml`, `dvc-release.yaml`)
- ✅ Set up S3 remote configuration for DVC
- ✅ Generate `pyproject.toml` (Poetry configuration with ruff and pytest)
- ✅ Create Dockerfile and CI/CD configurations
- ✅ Set up environment variable templates
- ✅ Generate test files (`tests/test_basic.py`, `tests/test_model.py`)

If you need to re-run bootstrap (this will overwrite existing files):
```bash
python3 .ml-aws-template/bootstrap.py --force
```

### 4. Install Poetry (if not already installed)

```bash
curl -sSL https://install.python-poetry.org | python3 -
# Add Poetry to PATH (add to ~/.bashrc or ~/.zshrc):
export PATH="$HOME/.local/bin:$PATH"
```

### 5. Install dependencies

```bash
poetry install
# Activate Poetry shell:
poetry shell
# Or run commands with Poetry:
poetry run python -m my_project.train
```

### 6. Configure AWS credentials

Configure AWS credentials using one of these methods:

- **AWS CLI**: `aws configure`
- **Environment variables**: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- **IAM roles**: If running on EC2/ECS

### 7. Initialize DVC (if not already done)

```bash
dvc init
```

## Getting Started with Development

After bootstrap and `poetry install`, you have working infrastructure (DVC pipelines, Docker, CI/CD, config management) but **stub code** that needs your implementation. Here's what to work on and in what order.

### Files to customize (in order)

| File | What to do |
|------|------------|
| `src/{module_name}/data/preprocess.py` | Read from `data/raw/`, organize images into `data/processed/{train,val,test}/<class>/` (ImageFolder layout) |
| `src/{module_name}/data/datamodule.py` | Adjust transforms and data augmentation in `default_train_transforms()` / `default_eval_transforms()` |
| `src/{module_name}/model/model.py` | Replace the placeholder 2-layer MLP with your architecture |
| `params.yaml` | Adjust hyperparameters (image_size, num_classes, batch_size, lr, max_epochs) to match your data |

### Files to leave alone

These are already wired up and don't need changes for most projects:

- `config.py`, `utils.py` — config loading and factory functions
- `train.py`, `eval.py` — training and evaluation entry points (use utils factories)
- `dvc.yaml`, `dvc-release.yaml` — pipeline definitions
- `Dockerfile`, `.circleci/config.yml` — build and CI/CD

### Verify your setup

```bash
# 1. Run smoke tests (should pass without any data)
poetry run pytest

# 2. Implement preprocess.py, then run it
dvc repro -s preprocess

# 3. Implement datamodule.py and model.py, then train
dvc repro -s train

# 4. Check training in TensorBoard
tensorboard --logdir logs

# 5. Run the full pipeline end-to-end
dvc repro
```

## Project Structure

After bootstrapping, your project will have the following structure:

```
my-new-ml-project/
├── .ml-aws-template/         # Template submodule (hidden, unchanged)
├── src/
│   └── {module_name}/
│       ├── train.py          # Training script
│       ├── eval.py           # Evaluation script
│       ├── data/
│       │   ├── preprocess.py
│       │   └── datamodule.py
│       ├── model/
│       │   └── model.py
│       └── scripts/          # Utility scripts
│           ├── export_and_benchmark.py
│           ├── register_model.py
│           └── release.py
├── dvc.yaml                  # Main DVC pipeline (preprocess → train → evaluate)
├── dvc-release.yaml          # Release pipeline (export → tag → upload)
├── params.yaml               # DVC parameters
├── pyproject.toml            # Poetry dependencies and package config
├── poetry.lock               # Locked dependency versions (generated)
├── Dockerfile                # Docker image for training
├── .dvc/config               # DVC S3 remote configuration
└── .env.example              # Environment variables template
```

## Usage

### Running the Training Pipeline

```bash
# Run the full pipeline: preprocess → train → evaluate
dvc repro

# Or run individual stages
dvc repro -s preprocess
dvc repro -s train
dvc repro -s evaluate
```

### Viewing Training Logs

TensorBoard logs are stored locally in the `logs/` directory:

```bash
tensorboard --logdir logs
```

Then open http://localhost:6006 in your browser.

### Model Release Pipeline

To release a model (export to ONNX, create git tag, upload to S3):

```bash
# Run the full release pipeline
dvc repro -f dvc-release.yaml

# Or run individual stages
python -m {module_name}.scripts.release export-onnx
python -m {module_name}.scripts.release create-tag
python -m {module_name}.scripts.release upload-s3
```

### Model Versioning

Models are versioned using git tags:

```bash
# Tag a model version
python -m {module_name}.scripts.register_model --tag production-candidate
```

This creates a git tag like `model-production-candidate-{commit_hash}`.

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

## Dependencies

Key dependencies included:

- `lightning` - Training framework (from Lightning AI)
- `torch`, `torchvision` - PyTorch
- `tensorboard` - Experiment tracking (local)
- `dvc[s3]` - Data version control with S3 support
- `boto3` - AWS SDK
- `onnx`, `onnxruntime-gpu` - ONNX export and inference
- `gitpython` - Git operations

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

## CI/CD

The template includes CircleCI configuration (`.circleci/config.yml`) for:

- Running tests
- Training and model registration
- Docker image building and pushing
- AWS Batch job submission

Configure CircleCI environment variables in your project settings.

## Docker

Build and run the training pipeline in Docker:

```bash
docker build -t my-ml-project .
docker run my-ml-project
```

The Dockerfile uses a multi-stage build with CUDA support for GPU training.

## Next Steps

See **Getting Started with Development** above for the files to implement first. Once your pipeline runs end-to-end (`dvc repro`):

1. **Track data with DVC**: `dvc add data/raw/` and push to S3 with `dvc push`
2. **Configure AWS**: Set up S3 buckets and IAM permissions (see `.env.example`)
3. **Release a model**: `dvc repro -f dvc-release.yaml` to export ONNX, tag, and upload to S3
4. **Set up CI/CD**: Configure CircleCI environment variables in your project settings

## License

See LICENSE file for details.
