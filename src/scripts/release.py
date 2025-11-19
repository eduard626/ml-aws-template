"""
Model release pipeline: Export to ONNX, create git tag, and upload to S3.
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import boto3
import torch
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
RELEASES_DIR = Path("releases")
RELEASES_DIR.mkdir(exist_ok=True)

MODEL_CKPT_PATH = Path("models/model.ckpt")
ONNX_PATH = RELEASES_DIR / "model.onnx"
MODEL_INFO_PATH = RELEASES_DIR / "model_info.json"
GIT_TAG_MARKER = RELEASES_DIR / ".git_tag_created"
S3_UPLOAD_MARKER = RELEASES_DIR / ".s3_upload_complete"

# S3 Configuration
S3_BUCKET = os.getenv("MODEL_RELEASE_S3_BUCKET", "ml-data")
S3_PREFIX = os.getenv("MODEL_RELEASE_S3_PREFIX", "models")  # Will be: s3://ml-data/models/{project_name}/{version}/


def load_params():
    """Load parameters from params.yaml"""
    with open("params.yaml", "r") as f:
        return yaml.safe_load(f)


def export_to_onnx():
    """Export PyTorch model to ONNX format"""
    print("🔄 Exporting model to ONNX...")
    
    # Load model checkpoint
    # TODO: Replace with your actual model class
    # Uncomment and adjust the import path:
    # from ${moduleName}.model.model import SimpleClassifier
    # model = SimpleClassifier.load_from_checkpoint(str(MODEL_CKPT_PATH))
    # model.eval()
    
    # Placeholder: Load a dummy model for now
    # In production, uncomment and use your actual model class
    class DummyModel(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.linear = torch.nn.Linear(784, 10)
        
        def forward(self, x):
            return self.linear(torch.flatten(x, 1))
    
    model = DummyModel()
    model.eval()
    
    # Load params for input shape
    params = load_params()
    # Default input shape, adjust based on your params.yaml
    input_shape = params.get("training", {}).get("input_shape", [1, 1, 28, 28])
    dummy_input = torch.randn(input_shape)
    
    # Export to ONNX
    torch.onnx.export(
        model,
        dummy_input,
        str(ONNX_PATH),
        export_params=True,
        opset_version=17,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={"input": {0: "batch_size"}, "output": {0: "batch_size"}},
    )
    
    print(f"✅ Model exported to ONNX: {ONNX_PATH}")
    
    # Create model_info.json
    params = load_params()
    model_info = {
        "version": get_version_from_git(),
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "model_path": str(MODEL_CKPT_PATH),
        "onnx_path": str(ONNX_PATH),
        "input_shape": input_shape,
        "training_params": params.get("training", {}),
        "git_commit": get_git_commit_hash(),
        "git_branch": get_git_branch(),
    }
    
    with open(MODEL_INFO_PATH, "w") as f:
        json.dump(model_info, f, indent=2)
    
    print(f"✅ Model info saved to: {MODEL_INFO_PATH}")
    return model_info


def get_version_from_git():
    """Get version from git tag or commit hash"""
    try:
        # Try to get the latest tag
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    
    # Fallback to commit hash
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return f"dev-{result.stdout.strip()}"
    except Exception:
        return "unknown"


def get_git_commit_hash():
    """Get current git commit hash"""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def get_git_branch():
    """Get current git branch"""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def create_git_tag():
    """Create a git tag for this release"""
    print("🔄 Creating git tag...")
    
    # Load model info to get version
    with open(MODEL_INFO_PATH, "r") as f:
        model_info = json.load(f)
    
    version = model_info["version"]
    
    # If version already starts with 'v', use it; otherwise add 'v'
    tag_name = version if version.startswith("v") else f"v{version}"
    
    try:
        # Check if tag already exists
        result = subprocess.run(
            ["git", "tag", "-l", tag_name],
            capture_output=True,
            text=True,
            check=True,
        )
        if result.stdout.strip():
            print(f"⚠️  Tag {tag_name} already exists. Skipping tag creation.")
        else:
            # Create annotated tag
            subprocess.run(
                ["git", "tag", "-a", tag_name, "-m", f"Release {tag_name}: Model exported and uploaded to S3"],
                check=True,
            )
            print(f"✅ Created git tag: {tag_name}")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Failed to create git tag: {e}")
        print("   Continuing without tag...")
    
    # Create marker file
    GIT_TAG_MARKER.touch()
    print(f"✅ Tag creation step completed")


def upload_to_s3():
    """Upload model files to S3"""
    print("🔄 Uploading model files to S3...")
    
    # Load model info
    with open(MODEL_INFO_PATH, "r") as f:
        model_info = json.load(f)
    
    version = model_info["version"]
    tag_name = version if version.startswith("v") else f"v{version}"
    
    # Get project name from current directory
    project_name = Path.cwd().name
    
    # S3 path: s3://ml-data/models/{project_name}/{version}/
    s3_key_prefix = f"{S3_PREFIX}/{project_name}/{tag_name}/"
    
    s3_client = boto3.client("s3")
    
    files_to_upload = [
        (ONNX_PATH, f"{s3_key_prefix}model.onnx"),
        (MODEL_CKPT_PATH, f"{s3_key_prefix}model.pth"),  # Upload PyTorch checkpoint as .pth
        (MODEL_INFO_PATH, f"{s3_key_prefix}model_info.json"),
    ]
    
    for local_path, s3_key in files_to_upload:
        if not local_path.exists():
            print(f"⚠️  File not found: {local_path}. Skipping...")
            continue
        
        try:
            print(f"   Uploading {local_path.name} to s3://{S3_BUCKET}/{s3_key}...")
            s3_client.upload_file(str(local_path), S3_BUCKET, s3_key)
            print(f"   ✅ Uploaded: {s3_key}")
        except Exception as e:
            print(f"   ❌ Failed to upload {local_path.name}: {e}")
            sys.exit(1)
    
    # Create marker file
    S3_UPLOAD_MARKER.touch()
    print(f"✅ All files uploaded to s3://{S3_BUCKET}/{s3_key_prefix}")
    print(f"   - model.onnx")
    print(f"   - model.pth")
    print(f"   - model_info.json")


def main():
    parser = argparse.ArgumentParser(description="Model release pipeline")
    parser.add_argument(
        "command",
        choices=["export-onnx", "create-tag", "upload-s3"],
        help="Release pipeline command to execute",
    )
    
    args = parser.parse_args()
    
    if args.command == "export-onnx":
        export_to_onnx()
    elif args.command == "create-tag":
        create_git_tag()
    elif args.command == "upload-s3":
        upload_to_s3()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

