# src/{{ moduleName }}/data/datamodule.py
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
import pytorch_lightning as pl
from pathlib import Path

# --- Custom Dataset ---
class MyDataset(Dataset):
    """
    A simple Dataset for loading Parquet files processed by the DVC stage.
    """
    def __init__(self, file_path: Path):
        print(f"Loading dataset from {file_path}")
        self.data = None
        self.targets = None
        self.features = None
        print(f"Dataset loaded from {file_path}")
        # TODO: Implement dataset loading logic

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.features[idx], self.targets[idx]

# --- Lightning DataModule ---
class MyDataModule(pl.LightningDataModule):
    """
    Encapsulates all data loading steps for PyTorch Lightning.
    """
    def __init__(self, data_dir: str = 'data/processed', batch_size: int = 32, num_workers: int = 4):
        super().__init__()
        self.data_dir = Path(data_dir)
        self.batch_size = batch_size
        self.num_workers = num_workers
        # Datasets initialized to None
        self.train_data = None
        self.val_data = None
        self.test_data = None

    # This method is for operations that should only run once (e.g., download data)
    def prepare_data(self):
        # We assume DVC has already run the preprocess stage, so files exist.
        # Use 'pass' if no single-process downloads/writes are needed.
        pass

    # This method runs on every GPU/process and is where Datasets are initialized
    def setup(self, stage: str):
        # Assign train/val datasets for use in dataloaders
        if stage == 'fit' or stage == 'validate':
            self.train_data = MyDataset(self.data_dir / 'train.parquet')
            self.val_data = MyDataset(self.data_dir / 'val.parquet')

        # Assign test dataset for use in dataloader(s)
        if stage == 'test':
            self.test_data = MyDataset(self.data_dir / 'test.parquet')

    def train_dataloader(self):
        return DataLoader(
            self.train_data, 
            batch_size=self.batch_size, 
            num_workers=self.num_workers,
            shuffle=True
        )

    def val_dataloader(self):
        return DataLoader(
            self.val_data, 
            batch_size=self.batch_size, 
            num_workers=self.num_workers,
            shuffle=False # No need to shuffle validation data
        )

    def test_dataloader(self):
        return DataLoader(
            self.test_data, 
            batch_size=self.batch_size, 
            num_workers=self.num_workers,
            shuffle=False
        )

# Example Usage (optional, for local testing)
if __name__ == '__main__':
    # This only works if you have run the DVC 'preprocess' stage first!
    # from {{ moduleName }}.train import train
    # train() # Run the DVC train stage to generate data/processed/
    
    # dm = MyDataModule()
    # dm.setup('fit')
    # print(f"First training batch shape: {next(iter(dm.train_dataloader()))[0].shape}")
    pass