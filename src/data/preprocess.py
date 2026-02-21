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

    Data workflow:
      - First time: manually place or download your raw data into data/raw/.
      - After preprocessing, track processed data with DVC:
            dvc add data/processed
            git add data/processed.dvc .gitignore
            git commit -m "Track processed data"
            dvc push
      - On other machines / CI: dvc pull to restore data from the S3 remote.
      - You can also track raw data: dvc add data/raw && dvc push
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

    # Ensure raw data exists before running preprocess
    if not raw_data_dir.exists() or not any(raw_data_dir.iterdir()):
        print("No raw data found in data/raw/.")
        print("Place your dataset there first, or download it in this script.")
        print("See the data workflow notes in preprocess() docstring.")
        raise SystemExit(1)

    processed_data_dir.mkdir(parents=True, exist_ok=True)
    preprocess(raw_data_dir, processed_data_dir, params)
