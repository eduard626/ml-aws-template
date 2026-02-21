#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
from pathlib import Path


# --- Utility functions ---

def run_command(cmd, cwd=None, allow_failure=False):
    print(f"  Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        if allow_failure:
            print(f"  Warning: command failed but continuing: {' '.join(cmd)}")
            return False
        print(f"  Error running command: {' '.join(cmd)}")
        sys.exit(result.returncode)
    return True


def replace_placeholders(content, module_name, project_name):
    """Replace ${moduleName} and ${projectName} template placeholders."""
    content = content.replace("${moduleName}", module_name)
    content = content.replace("${projectName}", project_name)
    return content


def copy_template_file(src_path, dest_path, module_name, project_name):
    """Copy a template file, replacing placeholders."""
    content = src_path.read_text()
    content = replace_placeholders(content, module_name, project_name)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_text(content)
    dest_path.chmod(0o644)


def clean_generated_files(project_dir):
    """Remove previously generated files before re-bootstrap."""
    files_to_remove = [
        ".gitignore", "pyproject.toml", "poetry.lock",
        "dvc.yaml", "dvc-release.yaml", "params.yaml", ".env.example",
        "Dockerfile", "docker_build.sh", ".circleci/config.yml", ".dvc/config",
    ]
    print("  Cleaning up generated files from project root...")
    for f in files_to_remove:
        target = Path(project_dir) / f
        if target.exists():
            target.unlink() if target.is_file() else shutil.rmtree(target)
            print(f"    Removed {f}")


# --- Template generators ---

def generate_pyproject_toml(project_name, module_name):
    """Generate pyproject.toml content with all dependencies and tool config."""
    return f'''[tool.poetry]
name = "{project_name}"
version = "0.1.0"
description = ""
authors = ["Your Name <your-email@example.com>"]

[[tool.poetry.source]]
name = "pytorch"
url = "https://download.pytorch.org/whl/cu128"
priority = "explicit"

[tool.poetry.dependencies]
python = ">=3.10,<4.0"
lightning = "^2.5.0"
torch = {{version = "2.7.1", source = "pytorch"}}
torchvision = {{version = "0.22.1", source = "pytorch"}}
torchmetrics = "^1.5.0"
tensorboard = "^2.18.0"
dvc = {{version = "^3.64.0", extras = ["s3"]}}
boto3 = "^1.35.0"
matplotlib = "^3.8.0"
numpy = "^1.26.0"
tqdm = "^4.66.0"
python-dotenv = "^1.0.0"
gitpython = "^3.1.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
ruff = "^0.9.0"

[tool.poetry.group.export]
optional = true

[tool.poetry.group.export.dependencies]
onnx = "^1.16.0"
onnxruntime = "^1.18.0"

[tool.poetry.group.cv]
optional = true

[tool.poetry.group.cv.dependencies]
timm = "^1.0.0"
albumentations = "^2.0.0"
pycocotools = "^2.0.0"

[tool.ruff]
line-length = 120
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
'''


def generate_gitignore():
    """Generate .gitignore content."""
    return """# Data and models (tracked by DVC)
data/
models/
releases/

# Logs
logs/

# DVC
.dvc/cache
.dvc/config.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
dist/
build/
*.egg

# Virtual environments
.venv/
venv/

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
*.DS_Store
.env

# Notebooks
notebooks/
.ipynb_checkpoints/
"""


def generate_test_basic(module_name):
    """Generate basic import test."""
    return f"""def test_import():
    import {module_name}
    assert 1 == 1
"""


# --- Main bootstrap logic ---

def main():
    project_dir = Path.cwd()
    project_name = project_dir.name
    module_name = project_name.replace("-", "_")
    print(f"--- Bootstrapping ML project in '{project_dir}' ---")
    print(f"Project name: {project_name}, Module name: {module_name}")

    # --- Check if already bootstrapped (unless --force is used) ---
    force = "--force" in sys.argv
    if not force:
        bootstrap_markers = ["src", "dvc.yaml", "pyproject.toml"]
        already_bootstrapped = any(
            (project_dir / marker).exists() for marker in bootstrap_markers
        )

        if already_bootstrapped:
            print("\n  This project appears to already be bootstrapped!")
            print("  Bootstrap is intended to be run only once for initial scaffolding.")
            print("  After bootstrap, you can freely edit pyproject.toml and other files.")
            print("\n  If you want to re-bootstrap (this will overwrite existing files):")
            print("    python3 .ml-aws-template/bootstrap.py --force")
            print("\n  Otherwise, to manage dependencies:")
            print("    - Edit pyproject.toml directly, or")
            print("    - Use poetry commands: poetry add <package> or poetry remove <package>")
            sys.exit(0)

    # --- Check Docker ---
    try:
        subprocess.run(
            ["docker", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        print("  Docker found.")
    except Exception:
        print("  Docker not found. Continuing without it.")

    # --- Cleanup any old generated files ---
    clean_generated_files(project_dir)

    # --- Locate template directory ---
    template_dir = project_dir / ".ml-aws-template"
    if not template_dir.exists():
        print(f"  Template directory not found: {template_dir}")
        print("  Make sure you've added this template as a submodule:")
        print("    git submodule add https://github.com/eduard626/ml-aws-template.git .ml-aws-template")
        sys.exit(1)

    template_configs = template_dir / "template_configs"
    template_src = template_dir / "src"

    if not template_configs.exists():
        print(f"  Warning: template_configs not found in {template_dir}")
    if not template_src.exists():
        print(f"  Warning: src not found in {template_dir}")

    # --- Generate pyproject.toml ---
    print("\n  Generating pyproject.toml...")
    pyproject_path = project_dir / "pyproject.toml"
    pyproject_path.write_text(generate_pyproject_toml(project_name, module_name))
    pyproject_path.chmod(0o644)
    print("    pyproject.toml")

    # --- Generate .gitignore ---
    print("  Generating .gitignore...")
    gitignore_path = project_dir / ".gitignore"
    gitignore_path.write_text(generate_gitignore())
    gitignore_path.chmod(0o644)
    print("    .gitignore")

    # --- Copy config files with placeholder replacement ---
    print("\n  Copying config files...")
    config_file_map = {
        "dvc.yaml": "dvc.yaml",
        "dvc-release.yaml": "dvc-release.yaml",
        "params.yaml": "params.yaml",
        "environment.env": ".env.example",
        "dvc_config": ".dvc/config",
        "circleci_config.yaml": ".circleci/config.yml",
        "Dockerfile": "Dockerfile",
        "docker_build.sh": "docker_build.sh",
    }

    for template_name, dest_name in config_file_map.items():
        src_path = template_configs / template_name
        dest_path = project_dir / dest_name
        if src_path.exists():
            copy_template_file(src_path, dest_path, module_name, project_name)
            print(f"    {dest_name}")
        else:
            print(f"    Warning: template not found: {template_name}")

    # Make shell scripts executable
    for script in ["docker_build.sh"]:
        script_path = project_dir / script
        if script_path.exists():
            script_path.chmod(0o755)

    # --- Copy Python source files ---
    print("\n  Copying Python source files...")
    src_dest = project_dir / "src" / module_name

    # Files that exist in the template src/ directory
    source_files = [
        "config.py",
        "utils.py",
        "train.py",
        "eval.py",
        "data/datamodule.py",
        "data/preprocess.py",
        "model/model.py",
        "scripts/__init__.py",
        "scripts/register_model.py",
        "scripts/export_and_benchmark.py",
        "scripts/release.py",
    ]

    for rel_path in source_files:
        src_path = template_src / rel_path
        dest_path = src_dest / rel_path
        if src_path.exists():
            copy_template_file(src_path, dest_path, module_name, project_name)
            print(f"    src/{module_name}/{rel_path}")
        else:
            print(f"    Warning: source template not found: {rel_path}")

    # Create __init__.py files for packages that don't have templates
    init_packages = ["", "data", "model"]
    for pkg in init_packages:
        init_path = src_dest / pkg / "__init__.py" if pkg else src_dest / "__init__.py"
        if not init_path.exists():
            init_path.parent.mkdir(parents=True, exist_ok=True)
            init_path.write_text("# Placeholder\n")
            init_path.chmod(0o644)

    # --- Generate test files ---
    print("\n  Generating test files...")
    tests_dir = project_dir / "tests"
    tests_dir.mkdir(exist_ok=True)

    # test_basic.py - import test
    test_basic_path = tests_dir / "test_basic.py"
    test_basic_path.write_text(generate_test_basic(module_name))
    test_basic_path.chmod(0o644)
    print("    tests/test_basic.py")

    # test_model.py - smoke test (from template)
    test_model_template = template_configs / "test_model.py"
    if test_model_template.exists():
        test_model_path = tests_dir / "test_model.py"
        copy_template_file(test_model_template, test_model_path, module_name, project_name)
        print("    tests/test_model.py")

    # --- Verify expected structure ---
    print("\n  Verifying project structure...")
    expected_files = [
        "pyproject.toml",
        ".gitignore",
        "Dockerfile",
        "docker_build.sh",
        "dvc.yaml",
        "dvc-release.yaml",
        "params.yaml",
        ".env.example",
        ".dvc/config",
        ".circleci/config.yml",
        "src",
        "tests",
    ]

    missing_files = []
    for item in expected_files:
        target = project_dir / item
        if not target.exists():
            missing_files.append(item)
        else:
            print(f"    OK  {item}")

    if missing_files:
        print(f"    Missing: {', '.join(missing_files)}")

    # --- Done ---
    print(f"\n  Project bootstrapped successfully!")
    print(f"\n  Project structure:")
    print(f"    {project_dir}/")
    print(f"    .ml-aws-template/       (template - unchanged, hidden)")
    print(f"    src/{module_name}/      (generated Python code)")
    print(f"    tests/                   (generated test files)")
    print(f"    pyproject.toml           (Poetry dependencies + ruff + pytest config)")
    print(f"    Dockerfile               (CUDA 12.8 multi-stage build)")
    print(f"    docker_build.sh          (export requirements + docker build)")
    print(f"    dvc.yaml                 (training pipeline)")
    print(f"    dvc-release.yaml         (release pipeline)")
    print(f"    params.yaml              (hyperparameters)")
    print(f"    .dvc/config              (S3 remote)")
    print(f"    .circleci/config.yml     (CI/CD pipeline)")
    print(f"    .env.example             (environment variables template)")
    print(f"    .gitignore")
    print(f"\n  Next steps:")
    print(f"    1. Install Poetry if not already installed:")
    print(f"       curl -sSL https://install.python-poetry.org | python3 -")
    print(f"    2. Install dependencies: poetry install")
    print(f"       Optional groups (install as needed):")
    print(f"         poetry install --with export    # ONNX export (onnx, onnxruntime)")
    print(f"         poetry install --with cv        # CV extras (timm, albumentations, pycocotools)")
    print(f"       Add your own deps: poetry add <package>")
    print(f"    3. Implement your code (look for TODO comments):")
    print(f"       a. src/{module_name}/data/preprocess.py  — raw images -> train/val/test splits")
    print(f"       b. src/{module_name}/data/datamodule.py  — load images as tensors")
    print(f"       c. src/{module_name}/model/model.py      — your model architecture")
    print(f"    4. Adjust params.yaml to match your data and model")
    print(f"    5. Run the full pipeline: dvc repro")
    print(f"    6. View training metrics: tensorboard --logdir logs")


if __name__ == "__main__":
    main()
