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

# Optional dependency groups (install as needed):
poetry install --with export    # ONNX export (onnx, onnxruntime)
poetry install --with cv        # CV extras (timm, albumentations, pycocotools)

# Add your own deps anytime:
poetry add <package>
```

See [Usage Guide - Dependencies](docs/guide.md#dependencies) for the full list and management commands.

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
| `src/{module_name}/data/preprocess.py` | Add your raw data to `data/raw/` first, then implement logic to organize into `data/processed/{train,val,test}/<class>/` (ImageFolder layout) |
| `src/{module_name}/data/datamodule.py` | Adjust transforms and data augmentation in `default_train_transforms()` / `default_eval_transforms()` |
| `src/{module_name}/model/model.py` | Replace the placeholder CNN with your architecture |
| `params.yaml` | Adjust hyperparameters (image_size, num_classes, batch_size, lr, max_epochs) to match your data |

### Files to leave alone

These are already wired up and don't need changes for most projects:

- `config.py`, `utils.py` — config loading and factory functions
- `train.py`, `eval.py` — training and evaluation entry points (use utils factories)
- `dvc.yaml`, `dvc-release.yaml` — pipeline definitions
- `Dockerfile`, `docker_build.sh`, `.circleci/config.yml` — build and CI/CD

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

### Data workflow

Raw data must be added manually the first time — the template does not auto-download any dataset.

```bash
# 1. Place or download your dataset into data/raw/
mkdir -p data/raw
# ... copy/download your images here ...

# 2. Run preprocessing to create train/val/test splits
dvc repro -s preprocess

# 3. Track processed data with DVC (so teammates can pull it)
dvc add data/processed
git add data/processed.dvc .gitignore
git commit -m "Track processed data"
dvc push

# 4. On another machine, restore data from S3:
dvc pull
```

You can also track raw data with `dvc add data/raw` if you want to version the original dataset.

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
├── docker_build.sh           # Export requirements + docker build
├── .dvc/config               # DVC S3 remote configuration
└── .env.example              # Environment variables template
```

## Next Steps

Once your pipeline runs end-to-end (`dvc repro`):

1. **Track data with DVC**: `dvc add data/raw/` and push to S3 with `dvc push`
2. **Configure AWS**: Set up S3 buckets and IAM permissions (see `.env.example`)
3. **Release a model**: `dvc repro -f dvc-release.yaml` to export ONNX, tag, and upload to S3
4. **Set up CI/CD**: Configure CircleCI environment variables in your project settings

For detailed usage, configuration, Docker, and dependency management, see the **[Usage Guide](docs/guide.md)**.

## License

See LICENSE file for details.
