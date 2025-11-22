#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
import re
from pathlib import Path

# --- Utility functions ---
def run_command(cmd, cwd=None, env=None, allow_failure=False):
    print(f"🚀 Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, env=env)
    if result.returncode != 0:
        if allow_failure:
            print(f"⚠️  Command failed but continuing: {' '.join(cmd)}")
            return False
        print(f"❌ Error running command: {' '.join(cmd)}")
        sys.exit(result.returncode)
    return True

def clean_projen_files(project_dir):
    """Remove Projen-managed files before reinitialization."""
    files_to_remove = [
        "package.json", "package-lock.json", ".gitattributes", ".gitignore",
        "pyproject.toml", "poetry.lock",
        "dvc.yaml", "params.yaml", ".env.example", "Dockerfile", 
        ".circleci/config.yml",
    ]
    print("🗑️  Cleaning up Projen-managed files from project root...")
    for f in files_to_remove:
        target = Path(project_dir) / f
        if target.exists():
            target.unlink() if target.is_file() else shutil.rmtree(target)
            print(f"   -> Removed {f}")
        else:
            print(f"   -> Skipping {f} (not found)")

def copy_template_scaffold(src_dir, dest_dir):
    print("📁 Copying template scaffolding to project root...")
    for item in os.listdir(src_dir):
        s = os.path.join(src_dir, item)
        d = os.path.join(dest_dir, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)

# --- Main bootstrap logic ---
def main():
    project_dir = Path.cwd()
    project_name = project_dir.name
    print(f"--- Bootstrapping ML project in '{project_dir}' ---")
    print(f"Project name: {project_name}, Module name: {project_name}")

    # --- Check if already bootstrapped (unless --force is used) ---
    import sys
    force = '--force' in sys.argv
    if not force:
        bootstrap_markers = ["src", "dvc.yaml", "pyproject.toml"]
        already_bootstrapped = any((project_dir / marker).exists() for marker in bootstrap_markers)
        
        if already_bootstrapped:
            print("\n⚠️  This project appears to already be bootstrapped!")
            print("   Bootstrap is intended to be run only once for initial scaffolding.")
            print("   After bootstrap, you can freely edit pyproject.toml and other files.")
            print("\n   If you want to re-bootstrap (this will overwrite existing files):")
            print("   python3 .ml-aws-template/boostrap.py --force")
            print("\n   Otherwise, to manage dependencies:")
            print("   - Edit pyproject.toml directly, or")
            print("   - Use poetry commands: poetry add <package> or poetry remove <package>")
            sys.exit(0)

    # --- Check Docker ---
    try:
        subprocess.run(["docker", "--version"], check=True, stdout=subprocess.PIPE)
        print("✅ Docker found.")
    except Exception:
        print("⚠️  Docker not found. Continuing without it.")

    # --- Cleanup any old generated files ---
    clean_projen_files(project_dir)

    # --- Locate template directory (should be .ml-aws-template submodule) ---
    template_dir = project_dir / ".ml-aws-template"
    if not template_dir.exists():
        print(f"❌ Template directory not found: {template_dir}")
        print("   Make sure you've added this template as a submodule:")
        print("   git submodule add https://github.com/eduard626/ml-aws-template.git .ml-aws-template")
        sys.exit(1)

    # --- Verify required template directories exist ---
    template_configs = template_dir / "template_configs"
    template_src = template_dir / "src"
    projenrc = template_dir / ".projenrc.js"
    
    if not template_configs.exists():
        print(f"⚠️  Warning: template_configs not found in {template_dir}")
    if not template_src.exists():
        print(f"⚠️  Warning: src not found in {template_dir}")
    
    # --- Copy .projenrc.js to project root (required for projen to run) ---
    if projenrc.exists():
        dest_projenrc = project_dir / ".projenrc.js"
        shutil.copy2(projenrc, dest_projenrc)
        print(f"✅ Copied .projenrc.js to project root")
    else:
        print(f"❌ .projenrc.js not found in {template_dir}")
        sys.exit(1)

    # --- Run Projen synthesis ---
    print("\n🔨 Running Projen synthesis...")
    env = os.environ.copy()
    # Set environment variable to prevent automatic dependency installation
    env['SKIP_VENV_INSTALL'] = '1'
    
    # Install projen locally in the project (needed for node .projenrc.js)
    print("   Installing projen locally...")
    install_success = run_command(["npm", "init", "-y"], cwd=project_dir, env=env, allow_failure=True)
    if install_success:
        run_command(["npm", "install", "projen"], cwd=project_dir, env=env, allow_failure=True)

    # Use node directly to run .projenrc.js
    # The .projenrc.js file will synthesize when run directly (see the conditional at the end)
    # SKIP_VENV_INSTALL env var prevents automatic dependency installation
    print("   Running projen synthesis via node (skipping dependency installation)...")
    success = run_command(["node", ".projenrc.js"], cwd=project_dir, env=env, allow_failure=False)
    
    if success:
        print("✅ Projen synthesis completed successfully")
    
    # Poetry generates pyproject.toml automatically - no need to fix comments
    # Users can manage dependencies via poetry commands or by editing pyproject.toml directly
    
    # Clean up node_modules and package files (not needed after synthesis)
    print("   Cleaning up temporary files...")
    for cleanup_item in ["node_modules", "package.json", "package-lock.json"]:
        cleanup_path = project_dir / cleanup_item
        if cleanup_path.exists():
            if cleanup_path.is_dir():
                shutil.rmtree(cleanup_path)
            else:
                cleanup_path.unlink()
            print(f"      -> Removed {cleanup_item}")
    
    # Check if files were actually generated
    required_files = ["dvc.yaml", "params.yaml", "Dockerfile", ".env.example", "pyproject.toml"]
    missing_required = [f for f in required_files if not (project_dir / f).exists()]
    
    if missing_required:
        print(f"\n⚠️  Warning: Required files are missing: {', '.join(missing_required)}")
        print("   This suggests projen synthesis may have failed before generating files.")
        print("   Files should be generated even if dependency installation fails.")
        print("\n   Attempting to diagnose the issue...")
        
        # Check if template files are accessible from the project root
        for check_file in ["dvc.yaml", "params.yaml", "Dockerfile"]:
            template_path = template_configs / check_file
            if template_path.exists():
                print(f"   ✅ Template accessible: {template_path}")
            else:
                print(f"   ❌ Template not found: {template_path}")
        
        print("\n   💡 Try running manually: node .projenrc.js")
        print("      This will show the actual error preventing file generation.")

    # Poetry generates pyproject.toml automatically - no manual patching needed

    # --- Verify expected structure ---
    print("\n📁 Verifying project structure...")
    expected_files = [
        "pyproject.toml",
        "Dockerfile",
        "dvc.yaml",
        "dvc-release.yaml",
        "params.yaml",
        ".env.example",
        ".dvc/config",
        "src",
    ]
    
    missing_files = []
    for item in expected_files:
        target = project_dir / item
        if not target.exists():
            missing_files.append(item)
        else:
            print(f"   ✅ {item}")
    
    if missing_files:
        print(f"   ⚠️  Missing files: {', '.join(missing_files)}")
    
    # Verify template directory is intact
    if (template_dir / ".projenrc.js").exists():
        print(f"   ✅ .ml-aws-template/ (template directory intact)")
    else:
        print(f"   ⚠️  Warning: .ml-aws-template/ may have been modified")

    # --- Done ---
    print("\n🎉 Project bootstrapped successfully!")
    print(f"\n📂 Project structure:")
    print(f"   {project_dir}/")
    print(f"   ├── .ml-aws-template/       (template - unchanged, hidden)")
    print(f"   ├── src/                    (generated Python code)")
    print(f"   ├── pyproject.toml           (generated - Poetry dependencies)")
    print(f"   ├── Dockerfile              (generated)")
    print(f"   ├── dvc.yaml                (generated - training pipeline)")
    print(f"   ├── dvc-release.yaml        (generated - release pipeline)")
    print(f"   ├── params.yaml             (generated)")
    print(f"   ├── .dvc/config             (generated - S3 remote: s3://ml-data/dvcstore/{project_dir.name}/)")
    print(f"   └── .env.example            (generated)")
    print(f"\n💡 Next steps:")
    print(f"   1. Install Poetry if not already installed: curl -sSL https://install.python-poetry.org | python3 -")
    print(f"   2. Install dependencies: poetry install")
    print(f"   3. Activate Poetry shell: poetry shell")
    print(f"      Or run commands with: poetry run <command>")
    print(f"   4. Configure AWS credentials (via AWS CLI, env vars, or IAM role)")
    print(f"   5. Review and customize the generated files")
    print(f"   6. Initialize DVC: dvc init (if not already done)")
    print(f"   7. Start developing your ML project!")

if __name__ == "__main__":
    main()
