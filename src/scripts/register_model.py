
import argparse
import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def register_model(tag: str):
    """
    Tags the current model checkpoint in git for versioning.
    This replaces MLflow model registry with git-based versioning.
    """
    model_path = Path("models/model.ckpt")
    
    if not model_path.exists():
        raise FileNotFoundError(f"Model checkpoint not found: {model_path}")
    
    print(f"Tagging model with tag: {tag}")
    
    try:
        # Get current git commit hash
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        commit_hash = result.stdout.strip()
        
        # Create a git tag for this model version
        tag_name = f"model-{tag}-{commit_hash[:8]}"
        
        # Check if tag already exists
        check_result = subprocess.run(
            ["git", "tag", "-l", tag_name],
            capture_output=True,
            text=True,
            check=True
        )
        
        if check_result.stdout.strip():
            print(f"⚠️  Tag {tag_name} already exists. Skipping tag creation.")
        else:
            # Create annotated tag
            subprocess.run(
                ["git", "tag", "-a", tag_name, "-m", f"Model version {tag} at commit {commit_hash}"],
                check=True
            )
            print(f"✅ Created git tag: {tag_name}")
            print(f"   Model checkpoint: {model_path}")
            print(f"   Commit: {commit_hash}")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during model tagging: {e}")
        raise
    except Exception as e:
        print(f"❌ Error during model registration: {e}")
        raise

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Tag model version in git.")
    parser.add_argument(
        '--tag', 
        default='candidate', 
        help='Custom tag to mark the model version (e.g., production-candidate).'
    )
    args = parser.parse_args()
    register_model(args.tag)