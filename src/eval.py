
import json
from pathlib import Path
from dotenv import load_dotenv

from ${moduleName}.config import Config
from ${moduleName}.utils import setup_logger, create_datamodule, create_model, create_trainer

# Load environment variables
load_dotenv()


def evaluate():
    """Main evaluation function."""
    # Load configuration
    config = Config()
    
    # Load model from checkpoint
    model_path = Path("models/model.ckpt")
    if not model_path.exists():
        raise FileNotFoundError(f"Model checkpoint not found: {model_path}. Run training first.")
    
    # Setup components
    logger = setup_logger(run_type="eval")
    model = create_model(config, checkpoint_path=str(model_path))
    datamodule = create_datamodule(config, stage="test")
    trainer = create_trainer(config, logger)
    # Uncomment for GPU: trainer = create_trainer(config, logger, accelerator='gpu', devices=1)
    
    # Run evaluation
    print(f"Starting evaluation - TensorBoard logs: {logger.log_dir}")
    results = trainer.test(model, datamodule=datamodule)
    
    # Save results
    results_path = Path("evaluation_results.json")
    with open(results_path, 'w') as f:
        json.dump(results[0], f, indent=2)
    
    print(f"✅ Evaluation completed. Results saved to {results_path}")
    print(f"   Metrics: {results[0]}")
    print(f"   View logs with: tensorboard --logdir logs")

if __name__ == '__main__':
    evaluate()

