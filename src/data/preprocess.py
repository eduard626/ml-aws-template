import yaml
from pathlib import Path


def preprocess(raw_data_dir: Path, processed_data_dir: Path, params: dict):
    """Preprocess raw data into train/val/test Parquet files.

    TODO: Implement your preprocessing logic here. Expected output:
      - processed_data_dir / "train.parquet"
      - processed_data_dir / "val.parquet"
      - processed_data_dir / "test.parquet"
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
