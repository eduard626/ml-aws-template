# Friction Notes: Object Detection with ml-aws-template

Dogfood test: Adapting the classification-focused template for **object detection**
(Penn-Fudan Pedestrian Detection + torchvision Faster R-CNN).

## Pain Points

### FRICTION 1: Template is classification-only by design
- `model.py` is a `SimpleClassifier` with `CrossEntropyLoss` — completely unusable for detection.
- `datamodule.py` hardcodes `ImageFolder` (class-label-per-folder) — detection needs bounding box annotations.
- `utils.py` factory functions hardcode `SimpleClassifier` and `MyDataModule` imports — can't swap model type without editing utils.
- `train.py`/`eval.py` assume `(x, y)` batch format — detection batches are `(images, targets)` where targets are dicts with boxes/labels.
- **Impact**: Every single source file needs rewriting. The template provides zero reusable code for non-classification tasks.

### FRICTION 2: preprocess.py assumes local raw data already exists
- The stub expects `data/raw/` to already contain data and just reorganizes it.
- For Penn-Fudan (and most real projects), you need to **download** the dataset first.
- No guidance or pattern for dataset download in the template.
- The `dvc.yaml` preprocess stage lists `data/raw/` as a dep, which doesn't exist until you put data there manually.

### FRICTION 3: No custom collate_fn support in datamodule
- Detection requires a custom `collate_fn` because targets have variable numbers of bounding boxes per image.
- The default PyTorch collate tries to stack everything into tensors and crashes.
- The template's `MyDataModule` has no hook/parameter for custom collation.

### FRICTION 4: Detection models have dual-mode forward behavior
- torchvision detection models return **losses** during training (when targets are provided) and **predictions** during eval.
- Lightning's `training_step`/`validation_step` pattern doesn't cleanly map to this.
- The template's `forward()` → `loss_fn()` pattern is wrong for detection.

### FRICTION 5: params.yaml has classification-specific defaults
- `image_size: [28, 28]` — detection doesn't resize to a fixed size (uses multi-scale).
- `num_channels: 1` — Penn-Fudan is RGB (3 channels), and most real datasets are too.
- `num_classes: 10` — meaningless default for detection (Penn-Fudan has 2: background + pedestrian).
- No detection-specific params like `score_threshold`, `nms_threshold`, `anchor_sizes`, etc.

### FRICTION 6: eval.py assumes `trainer.test()` returns flat metrics dict
- For detection, evaluation produces per-class mAP, mAP@50, mAP@75, etc.
- The template's `results[0]` → `json.dump` pattern works but the structure is different from what a classification user might expect.

### FRICTION 7: test_model.py hardcodes classification assertions
- `assert out.shape == (2, 10)` — detection outputs are lists of dicts, not tensors.
- Test needs complete rewrite for detection model signature.

### FRICTION 8: No `torchmetrics.detection.MeanAveragePrecision` or pycocotools in deps
- Detection mAP evaluation needs pycocotools (and torchmetrics wraps it).
- Neither is in the template's dependencies — user must figure this out.
- pycocotools also needs system-level build tools (gcc, etc.) on some platforms.

### FRICTION 9: `compute_input_dim()` in config.py is classification-only
- Computes `image_size[0] * image_size[1] * num_channels` — only useful for MLP classifiers.
- No equivalent utility for detection (anchor generation, feature map sizes, etc.).
- Minor: at least it's documented as "CNN models typically don't need this."

### FRICTION 10: pyproject.toml needs manual editing to add new deps
- Had to manually add `pycocotools` to pyproject.toml.
- No guidance in template docs about what extra deps common task types need.
- bootstrap.py generates pyproject.toml as a Python f-string — can't extend it without editing bootstrap source.

### FRICTION 11: OOM with default batch_size on detection models
- Default `batch_size: 32` (classification default) causes immediate OOM with Faster R-CNN.
- Even `batch_size: 4` OOM'd on RTX 3080 (10GB) with full-resolution Penn-Fudan images (~560x720).
- Had to reduce to `batch_size: 2` + add image resizing (`max_image_size: 512`).
- The template has no guidance about memory-intensive architectures or image resolution trade-offs.
- Detection images vary in size — need custom resize logic that also scales bounding boxes, which the template's simple `transforms.Resize()` can't handle.

### FRICTION 12: No `max_image_size` param in config/datamodule
- Had to manually add `max_image_size` to params.yaml, pass through utils.py, and implement resize+box-scaling in the dataset.
- This is a common detection concern the template doesn't address.

### FRICTION 13: train.py and eval.py were reusable as-is (POSITIVE)
- Despite the template being classification-focused, `train.py` and `eval.py` worked without changes.
- The factory pattern in `utils.py` (create_model, create_datamodule, create_trainer) provided enough indirection.
- Only needed to update `utils.py` imports and parameters — the entry points stayed clean.
- `config.py` also worked unchanged.

### FRICTION 14: DVC pipeline worked with detection (POSITIVE)
- The `dvc.yaml` structure (preprocess -> train -> evaluate) mapped perfectly to detection.
- DVC commands with `poetry run` prefix worked correctly.
- `src/` prefix in dep paths was correct.

---

## Summary

The template works well for its designed use case (image classification with ImageFolder),
but adapting to any other task (detection, segmentation, generation, NLP) requires
rewriting **every generated source file**. The only things that survive unchanged are:
- `config.py` (config loading is generic enough)
- `dvc.yaml` / `dvc-release.yaml` (pipeline structure is task-agnostic)
- `Dockerfile`, CI/CD config
- Project structure (src layout, tests dir)

## Suggestions for Future Improvement
- Consider a `--task-type` flag for bootstrap (classification, detection, segmentation)
- Make utils.py factory functions configurable via registry pattern instead of hardcoded imports
- Add a `download_data()` hook in preprocess.py
- Document what needs changing for non-classification tasks
