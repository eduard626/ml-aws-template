import torch
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import lightning.pytorch as pl
from pathlib import Path


def default_train_transforms(image_size: tuple = (224, 224)):
    """Default training transforms with data augmentation.

    TODO: Adjust augmentation to match your dataset (e.g., larger crops,
          color jitter, normalization stats from your data).
    """
    return transforms.Compose([
        transforms.Resize(image_size),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        # TODO: Replace with your dataset's mean/std
        # transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])


def default_eval_transforms(image_size: tuple = (224, 224)):
    """Default evaluation transforms (no augmentation)."""
    return transforms.Compose([
        transforms.Resize(image_size),
        transforms.ToTensor(),
        # TODO: Replace with your dataset's mean/std (must match training)
        # transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])


# --- Lightning DataModule ---
class MyDataModule(pl.LightningDataModule):
    """
    Encapsulates all data loading steps for Lightning.

    Expects an ImageFolder-style directory layout under data_dir:
        data/processed/train/<class_name>/*.{png,jpg,...}
        data/processed/val/<class_name>/*.{png,jpg,...}
        data/processed/test/<class_name>/*.{png,jpg,...}
    """
    def __init__(self, data_dir: str = 'data/processed', batch_size: int = 32,
                 num_workers: int = 4, image_size: tuple = (224, 224)):
        super().__init__()
        self.data_dir = Path(data_dir)
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.image_size = image_size
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
            self.train_data = datasets.ImageFolder(
                self.data_dir / 'train',
                transform=default_train_transforms(self.image_size),
            )
            self.val_data = datasets.ImageFolder(
                self.data_dir / 'val',
                transform=default_eval_transforms(self.image_size),
            )

        # Assign test dataset for use in dataloader(s)
        if stage == 'test':
            self.test_data = datasets.ImageFolder(
                self.data_dir / 'test',
                transform=default_eval_transforms(self.image_size),
            )

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
            shuffle=False
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
    # dm = MyDataModule()
    # dm.setup('fit')
    # print(f"First training batch shape: {next(iter(dm.train_dataloader()))[0].shape}")
    pass
