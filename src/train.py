
import os
import yaml
import pytorch_lightning as pl
from pytorch_lightning.loggers import TensorBoardLogger
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime

# Placeholder imports (MUST be uncommented and adjusted)
# from ${moduleName}.model.model import SimpleClassifier 
# from ${moduleName}.data.datamodule import MyDataModule 

# Load environment variables
load_dotenv() 

def train():
    # 1. Load DVC parameters
    with open('params.yaml', 'r') as f:
        params = yaml.safe_load(f)['training']

    # 2. Setup TensorBoard logger (local only)
    # TensorBoard logs are stored in ./logs/ directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create a unique run name with timestamp
    run_name = f"train_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    tb_logger = TensorBoardLogger(
        save_dir=str(log_dir),
        name=run_name,
    )

    # 3. Setup Data and Model (Placeholders)
    # dm = MyDataModule(batch_size=params['batch_size'])
    # model = SimpleClassifier(lr=params['lr'])
    
    # 💡 Temporary placeholder setup for demonstration
    class MyDataModule:
        def __init__(self, batch_size): print(f"DataModule setup with batch_size={batch_size}")
    class SimpleClassifier:
        def __init__(self, lr): print(f"Model setup with lr={lr}")
        def eval(self): pass
    
    dm = MyDataModule(batch_size=params['batch_size'])
    model = SimpleClassifier(lr=params['lr'])
    # ----------------------------------------------------

    # 4. Setup Trainer with TensorBoard logger
    trainer = pl.Trainer(
        max_epochs=params['max_epochs'],
        logger=tb_logger,
        # accelerator='gpu', devices=1, # Uncomment for GPU training
    )

    print(f"Starting training - TensorBoard logs: {tb_logger.log_dir}")
    
    # 5. Run training (Placeholder: replace with actual call)
    # trainer.fit(model, datamodule=dm)
    
    # 6. Save the final model checkpoint
    # The model checkpoint is saved by DVC pipeline to models/model.ckpt
    # trainer.save_checkpoint("models/model.ckpt")
    
    print(f"✅ Training completed. View logs with: tensorboard --logdir {log_dir}")

if __name__ == "__main__":
    train()