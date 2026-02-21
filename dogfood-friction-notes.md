# Template Dogfood: Friction Notes

Tested by bootstrapping a Fashion MNIST autoencoder project at `/tmp/simple-autoencoder` using a timm `resnet18` encoder with a custom convolutional decoder. Went from bootstrap → preprocess → train → eval → TensorBoard verification.

**Result**: Training converged (MSE loss ~0.005), reconstruction images logged to TensorBoard, eval pipeline works. Total implementation time was dominated by working around template issues, not ML work.

---

## Critical Issues (would block a new user)

### 1. `onnxruntime-gpu` fails to install on most systems
**Severity**: Blocker
**What happens**: `poetry install` fails because `onnxruntime-gpu` wheels require CUDA system libraries at install time. Even switching to `onnxruntime` can fail due to ABI tag conflicts with the PyTorch cu128 source.
**Fix**: Make it optional (`[tool.poetry.group.export.dependencies]`) or default to `onnxruntime` (CPU) with a comment about the GPU variant. Most users won't need ONNX export during initial development.

### 2. `params.yaml` uses Python tuple syntax `(28, 28)` instead of YAML list
**Severity**: Silent bug
**What happens**: `image_size: (28, 28)` is parsed by YAML as the *string* `"(28, 28)"`, not a list/tuple. The code in `utils.py` checks `isinstance(image_size, list)` which is False for a string. This would cause `transforms.Resize("(28, 28)")` → crash.
**Fix**: Use YAML list syntax: `image_size: [28, 28]`

### 3. DVC dep paths don't include `src/` prefix
**Severity**: DVC breaks
**What happens**: `dvc.yaml` references `simple_autoencoder/train.py` but the file is at `src/simple_autoencoder/train.py`. DVC can't track these dependencies.
**Fix**: Template should generate paths with `src/` prefix: `src/${moduleName}/train.py`

### 4. DVC commands missing `poetry run`
**Severity**: DVC stages fail
**What happens**: `dvc.yaml` uses `cmd: python -m simple_autoencoder.train` but outside the Poetry virtualenv, the module isn't on PYTHONPATH. Running `dvc repro` directly would fail with `ModuleNotFoundError`.
**Fix**: Prefix commands with `poetry run`: `cmd: poetry run python -m simple_autoencoder.train`

---

## Medium Issues (cause confusion or extra work)

### 5. No `model` section support in Config class
**Severity**: Inconvenient
**What happens**: `config.py` has hardcoded properties for `data`, `training`, `evaluation`, `release` but no `model` section. Adding model-specific config (encoder name, pretrained flag, latent dim) requires using the generic `config.get('model', {})` instead of `config.model`.
**Suggestion**: Either add a `model` property, or make Config more dynamic (e.g., `__getattr__` that delegates to `_params`).

### 6. Template is classification-only — no guidance for other tasks
**Severity**: Design friction
**What happens**: The model template has `training_step` that unpacks `(x, y)` and uses `CrossEntropyLoss`. The eval script saves accuracy metrics. For autoencoders, GANs, or regression tasks, users must rewrite the training loop, loss, and evaluation from scratch.
**Suggestion**: Add comments noting what to change for non-classification tasks, or provide a `--task-type` flag to bootstrap (classification/reconstruction/regression).

### 7. No common pretrained-model libraries in default deps
**Severity**: Extra step for most users
**What happens**: `timm`, `transformers`, and `huggingface_hub` aren't in the generated `pyproject.toml`. Most modern ML projects use pretrained backbones, so `poetry add timm` is almost always the first thing a user does after bootstrap.
**Suggestion**: Include `timm` as a default dependency (or at least as a commented-out option).

---

## Minor Issues (polish)

### 8. DVC preprocess stage depends on `data/raw/` which doesn't exist yet
**What happens**: `dvc repro` would fail at the preprocess stage because `data/raw/` is listed as a dep but doesn't exist until the preprocess script creates it (e.g., downloading Fashion MNIST).
**Fix**: Remove `data/raw/` from deps or document that users should create it first.

### 9. No GPU auto-detection in train.py
**What happens**: The generated `train.py` has GPU usage commented out: `# Uncomment for GPU: trainer = create_trainer(config, logger, accelerator='gpu', devices=1)`. Lightning auto-detects GPUs by default anyway, but the comment is misleading — Lightning used the GPU without uncommenting anything.
**Fix**: Remove the misleading comment, or add `accelerator='auto'` to the default trainer config.

### 10. `test_model.py` references `SimpleClassifier` hardcoded
**What happens**: After changing the model class name (e.g., to `SimpleAutoencoder`), the generated test file still imports `SimpleClassifier`. Tests break immediately.
**Note**: This is inherent to the template approach — the test is generated once. Maybe the test could be more generic or use a factory function.

### 11. Preprocessing is slow for ImageFolder layout
**What happens**: Converting Fashion MNIST (70k images) to individual PNG files in ImageFolder layout took ~7 seconds. For larger datasets this would be very slow. The template's preprocess → ImageFolder → DataLoader pipeline adds overhead vs. using torchvision datasets directly.
**Note**: This is a design tradeoff — ImageFolder is universal and DVC-friendly, but it's not the fastest path for well-known datasets.

---

## What Worked Well

- Bootstrap itself is clean and fast — one command, clear output, good directory structure
- Lightning integration is solid — Trainer, DataModule, LightningModule patterns are correct
- TensorBoard logging works out of the box
- Poetry dependency management (besides onnxruntime) was smooth
- The factory pattern in `utils.py` is a good abstraction
- Config centralization in `params.yaml` is the right pattern
- The "next steps" printed after bootstrap are helpful
