
import os
import yaml
import mlflow
import pytorch_lightning as pl
from pytorch_lightning.loggers import MLflowLogger
from dotenv import load_dotenv
from pathlib import Path

# Placeholder imports (MUST be uncommented and adjusted)
# from {{ moduleName }}.model.model import SimpleClassifier 
# from {{ moduleName }}.data.datamodule import MyDataModule 

# Load environment variables (MLFLOW_TRACKING_URI, etc.)
load_dotenv() 

def train():
    # 1. Load DVC parameters
    with open('params.yaml', 'r') as f:
        params = yaml.safe_load()['training']

    # 2. Setup MLflow
    # MLflow automatically uses env vars like MLFLOW_TRACKING_URI
    mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT_NAME", "Default-Experiment"))
    
    with mlflow.start_run() as run:
        run_id = run.info.run_id
        
        # Log DVC params to MLflow
        mlflow.log_params(params)

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

        # 4. Set up Lightning MLflow Logger
        mlf_logger = MLflowLogger(
            experiment_name=mlflow.get_experiment(mlflow.last_active_run().info.experiment_id).name,
            run_id=run_id,
        )

        # 5. Setup Trainer (Placeholder)
        trainer = pl.Trainer(
            max_epochs=params['max_epochs'],
            logger=mlf_logger,
            # accelerator='gpu', devices=1, # Uncomment for GPU training
        )

        print(f"Starting training with MLflow Run ID: {run_id}")
        
        # 6. Run training (Placeholder: replace with actual call)
        # trainer.fit(model, datamodule=dm)
        
        # 7. Log the final model checkpoint artifact
        # This is where the model is saved and registered by MLflow
        # trainer.save_checkpoint("models/final_model.ckpt")
        # mlflow.pytorch.log_model(
        #     pytorch_model=model,
        #     artifact_path="model", 
        #     registered_model_name=os.getenv("MLFLOW_MODEL_NAME", "{{ moduleName }}")
        # )
        
        # 💡 IMPORTANT: Print the RUN_ID for CI to capture
        print(f"MLflow Run ID: {run_id}")

if __name__ == "__main__":
    train()