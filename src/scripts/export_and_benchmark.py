
import argparse
import time
import json
import os
import torch
import onnxruntime
import numpy as np
from tqdm import tqdm
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Configuration ---
MODEL_CKPT_PATH = Path("models/model.ckpt")
ONNX_FILE_NAME = "model.onnx"
BENCHMARK_OUTPUT = "benchmark_results.json"
# Define the size of your input tensor for tracing (e.g., 1 image, 1 channel, 28x28)
DUMMY_INPUT_SIZE = (1, 1, 28, 28) 
# ---------------------

# --- Benchmarking Function ---
def benchmark(model_runner, input_data, iterations=100, backend_name="Model"):
    latencies = []
    for _ in range(10): 
        _ = model_runner(input_data)  # Warm-up

    for _ in tqdm(range(iterations), desc=f"Benchmarking {backend_name}"):
        start = time.time()
        _ = model_runner(input_data)
        latencies.append(time.time() - start)

    mean_latency = np.mean(latencies) * 1000
    throughput = 1 / mean_latency * 1000
    return mean_latency, throughput


def run_export_and_benchmark():
    # 1. Load model checkpoint (local file)
    if not MODEL_CKPT_PATH.exists():
        raise FileNotFoundError(f"Model checkpoint not found: {MODEL_CKPT_PATH}")
    
    # 2. Load Model
    from ${moduleName}.model.model import SimpleClassifier
    model = SimpleClassifier.load_from_checkpoint(str(MODEL_CKPT_PATH))
    model.eval()
    
    # 3. Export to ONNX
    dummy_input = torch.randn(DUMMY_INPUT_SIZE, requires_grad=False)
    onnx_path = Path(ONNX_FILE_NAME)
    
    torch.onnx.export(
        model, dummy_input, str(onnx_path), export_params=True, opset_version=17, 
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
    
    # 5. Save benchmark results to JSON
    results = {
        "pt_latency_ms": float(pt_latency),
        "pt_throughput_qps": float(pt_throughput),
        "onnx_latency_ms": float(onnx_latency),
        "onnx_throughput_qps": float(onnx_throughput),
        "speedup": float(pt_latency / onnx_latency) if onnx_latency > 0 else 0.0
    }
    
    with open(BENCHMARK_OUTPUT, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"✅ Benchmark results saved to {BENCHMARK_OUTPUT}")
    print(f"   PyTorch latency: {pt_latency:.2f} ms, throughput: {pt_throughput:.2f} qps")
    print(f"   ONNX latency: {onnx_latency:.2f} ms, throughput: {onnx_throughput:.2f} qps")
    print(f"   Speedup: {results['speedup']:.2f}x")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Export PyTorch model to ONNX and benchmark.")
    args = parser.parse_args()
    run_export_and_benchmark()