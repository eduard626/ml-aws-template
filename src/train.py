
from pathlib import Path
from dotenv import load_dotenv

from ${moduleName}.config import Config
from ${moduleName}.utils import setup_logger, create_datamodule, create_model, create_trainer

# Load environment variables
load_dotenv()


def train():
    """Main training function."""
    # Load configuration
    config = Config()
    
    # Setup components
    logger = setup_logger(run_type="train")
    datamodule = create_datamodule(config, stage="fit")
    model = create_model(config)
    trainer = create_trainer(config, logger)
    # Uncomment for GPU: trainer = create_trainer(config, logger, accelerator='gpu', devices=1)
    
    # Run training
    print(f"Starting training - TensorBoard logs: {logger.log_dir}")
    trainer.fit(model, datamodule=datamodule)
    
    # Save checkpoint
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    trainer.save_checkpoint("models/model.ckpt")
    
    print(f"✅ Training completed. View logs with: tensorboard --logdir logs")

if __name__ == "__main__":
    train()