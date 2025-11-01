
import argparse
import time
import os
import torch
import onnxruntime
import numpy as np
from tqdm import tqdm
import mlflow
from pathlib import Path

# --- Configuration ---
MODEL_ARTIFACT_PATH = "model/model.ckpt"
ONNX_FILE_NAME = "model.onnx"
# Define the size of your input tensor for tracing (e.g., 1 image, 1 channel, 28x28)
DUMMY_INPUT_SIZE = (1, 1, 28, 28) 
# ---------------------

# --- Benchmarking Function (as previously defined) ---
def benchmark(model_runner, input_data, iterations=100, backend_name="Model"):
    # ... (Benchmark logic remains the same) ...
    latencies = []
    for _ in range(10): _ = model_runner(input_data) # Warm-up

    for _ in tqdm(range(iterations), desc=f"Benchmarking {backend_name}"):
        start = time.time()
        _ = model_runner(input_data)
        latencies.append(time.time() - start)

    mean_latency = np.mean(latencies) * 1000
    throughput = 1 / mean_latency * 1000
    return mean_latency, throughput
# ------------------------------------------------------


def run_export_and_benchmark(run_id: str):
    # Setup MLflow client and download artifact
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI"))
    
    # 1. Download Checkpoint
    local_dir = Path("./onnx_export_temp") / run_id
    local_dir.mkdir(parents=True, exist_ok=True)
    mlflow.artifacts.download_artifacts(
        run_id=run_id, 
        artifact_path=MODEL_ARTIFACT_PATH, 
        dst_path=local_dir
    )
    checkpoint_path = local_dir / Path(MODEL_ARTIFACT_PATH).name
    
    # 2. Load Model
    # 💡 REPLACE with your actual model class loading
    # from {{ moduleName }}.model.model import SimpleClassifier 
    # model = SimpleClassifier.load_from_checkpoint(checkpoint_path) 
    # model.eval() 
    
    # Placeholder: Use a dummy model for tracing
    class DummyModel(torch.nn.Module):
        def __init__(self): super().__init__(); self.linear = torch.nn.Linear(784, 10)
        def forward(self, x): return self.linear(torch.flatten(x, 1))
    model = DummyModel()
    model.eval()
    
    # 3. Export to ONNX
    dummy_input = torch.randn(DUMMY_INPUT_SIZE, requires_grad=False)
    onnx_path = local_dir / ONNX_FILE_NAME
    
    torch.onnx.export(
        model, dummy_input, onnx_path, export_params=True, opset_version=17, 
        input_names=['input'], output_names=['output'], 
        dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}}
    )
    print(f"✅ Model exported to ONNX: {onnx_path}")
    
    # 4. Validation and Benchmarking
    torch_runner = lambda x: model(x).cpu().detach().numpy()
    pt_latency, pt_throughput = benchmark(torch_runner, dummy_input, backend_name="PyTorch")
    
    ort_session = onnxruntime.InferenceSession(str(onnx_path))
    def onnx_runner(x):
        ort_inputs = {ort_session.get_inputs()[0].name: x.cpu().numpy()}
        return ort_session.run(None, ort_inputs)
        
    onnx_latency, onnx_throughput = benchmark(onnx_runner, dummy_input, backend_name="ONNX Runtime")
    
    # 5. Log Results and Artifacts
    with mlflow.start_run(run_id=run_id):
        mlflow.log_metric("pt_latency_ms", pt_latency)
        mlflow.log_metric("onnx_latency_ms", onnx_latency)
        mlflow.log_artifact(str(onnx_path), artifact_path="model_onnx")
        print("✅ ONNX model and metrics logged to MLflow.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Export PyTorch model to ONNX and benchmark.")
    parser.add_argument('--run-id', required=True, help='The MLflow Run ID containing the trained model.')
    args = parser.parse_args()
    run_export_and_benchmark(args.run_id)