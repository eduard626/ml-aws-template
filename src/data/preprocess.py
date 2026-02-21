import yaml
from pathlib import Path


def preprocess(raw_data_dir: Path, processed_data_dir: Path, params: dict):
    """Preprocess raw images into train/val/test splits.

    TODO: Implement your preprocessing logic here. Expected output layout
    (ImageFolder convention):
      - processed_data_dir / "train" / "<class_name>" / *.{png,jpg,...}
      - processed_data_dir / "val"   / "<class_name>" / *.{png,jpg,...}
      - processed_data_dir / "test"  / "<class_name>" / *.{png,jpg,...}

    Common steps:
      1. Read images from raw_data_dir (e.g. one folder per class, or a CSV manifest).
      2. Apply any resizing, cropping, or format conversion.
      3. Split into train/val/test and copy/symlink into the layout above.
    """
    raise NotImplementedError(
        "Preprocessing not implemented yet. "
        "Edit src/${moduleName}/data/preprocess.py to add your logic."
    )


if __name__ == "__main__":
    with open("params.yaml", "r") as f:
        params = yaml.safe_load(f)

    raw_data_dir = Path("data/raw")
    processed_data_dir = Path("data/processed")
    processed_data_dir.mkdir(parents=True, exist_ok=True)

    preprocess(raw_data_dir, processed_data_dir, params)
