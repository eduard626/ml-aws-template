"""
Utility functions for setting up PyTorch Lightning components.
"""
import pytorch_lightning as pl
from pytorch_lightning.loggers import TensorBoardLogger
from pathlib import Path
from datetime import datetime
from typing import Optional

from ${moduleName}.model.model import SimpleClassifier
from ${moduleName}.data.datamodule import MyDataModule
from ${moduleName}.config import Config


def setup_logger(run_type: str = "train", log_dir: Path = Path("logs")) -> TensorBoardLogger:
    """Setup TensorBoard logger.
    
    Args:
        run_type: Type of run ('train' or 'eval')
        log_dir: Directory to store logs
        
    Returns:
        Configured TensorBoardLogger
    """
    log_dir.mkdir(exist_ok=True)
    run_name = f"{run_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    return TensorBoardLogger(save_dir=str(log_dir), name=run_name)


def create_datamodule(config: Config, stage: str = "fit") -> MyDataModule:
    """Create and setup DataModule.
    
    Args:
        config: Configuration object
        stage: Setup stage ('fit', 'validate', or 'test')
        
    Returns:
        Configured and setup DataModule
    """
    if stage == "test":
        params = config.evaluation
    else:
        params = config.training
    
    dm = MyDataModule(
        data_dir='data/processed',
        batch_size=params.get('batch_size', 32),
        num_workers=params.get('num_workers', 4)
    )
    dm.setup(stage)
    return dm


def create_model(config: Config, checkpoint_path: Optional[str] = None) -> SimpleClassifier:
    """Create model instance.
    
    Args:
        config: Configuration object
        checkpoint_path: Optional path to checkpoint for loading
        
    Returns:
        Model instance
    """
    training_params = config.training
    input_dim = config.compute_input_dim()
    num_classes = config.data.get('num_classes', 10)
    
    if checkpoint_path and Path(checkpoint_path).exists():
        # Load from checkpoint
        model = SimpleClassifier.load_from_checkpoint(
            checkpoint_path,
            lr=training_params.get('lr', 0.001),
            input_dim=input_dim,
            num_classes=num_classes
        )
        model.eval()
    else:
        # Create new model
        model = SimpleClassifier(
            lr=training_params.get('lr', 0.001),
            input_dim=input_dim,
            num_classes=num_classes
        )
    
    return model


def create_trainer(
    config: Config,
    logger: TensorBoardLogger,
    max_epochs: Optional[int] = None,
    accelerator: Optional[str] = None,
    devices: Optional[int] = None
) -> pl.Trainer:
    """Create PyTorch Lightning Trainer.
    
    Args:
        config: Configuration object
        logger: Logger instance
        max_epochs: Override max_epochs from config
        accelerator: Accelerator type ('gpu', 'cpu', etc.)
        devices: Number of devices
        
    Returns:
        Configured Trainer
    """
    training_params = config.training
    
    trainer_kwargs = {
        'logger': logger,
        'max_epochs': max_epochs or training_params.get('max_epochs', 10),
    }
    
    # Add accelerator config if provided
    if accelerator:
        trainer_kwargs['accelerator'] = accelerator
    if devices is not None:
        trainer_kwargs['devices'] = devices
    
    return pl.Trainer(**trainer_kwargs)

