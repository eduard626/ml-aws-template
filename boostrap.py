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

    # --- Post-process generated files ---
    print("\n🔧 Post-processing generated files...")
    
    # Fix pyproject.toml comment to indicate users should edit the file directly
    pyproject_path = project_dir / "pyproject.toml"
    if pyproject_path.exists():
        try:
            with open(pyproject_path, 'r') as f:
                content = f.read()
            
            # Replace the projen-generated comment with a user-friendly one
            old_comment = r'# ~~ Generated by projen\. To modify, edit \.projenrc\.py and run "npx projen"\.'
            new_comment = '# This file was generated during bootstrap. You can edit it directly to manage dependencies.'
            
            if re.search(old_comment, content):
                content = re.sub(old_comment, new_comment, content)
            
            # Fix Python version constraint to >=3.10,<4.0
            python_version_pattern = r'python = "\^3\.8"'
            if re.search(python_version_pattern, content):
                content = re.sub(python_version_pattern, 'python = ">=3.10,<4.0"', content)
                print("   ✅ Updated Python version constraint to >=3.10,<4.0")
            
            # Fix dvc[s3] format - Projen generates "dvc[s3]" but Poetry needs dvc = {extras = ["s3"]}
            dvc_pattern = r'"dvc\[s3\]" = "([^"]+)"'
            if re.search(dvc_pattern, content):
                dvc_match = re.search(dvc_pattern, content)
                if dvc_match:
                    dvc_version = dvc_match.group(1)
                    content = re.sub(dvc_pattern, f'dvc = {{version = "{dvc_version}", extras = ["s3"]}}', content)
                    print("   ✅ Fixed dvc[s3] format in pyproject.toml")
            
            # Add PyTorch source URL (fixed to CUDA 12.8) with explicit priority
            # Only torch and torchvision will use this source
            pytorch_url = "https://download.pytorch.org/whl/cu128"
            pytorch_source = f'[[tool.poetry.source]]\nname = "pytorch"\nurl = "{pytorch_url}"\npriority = "explicit"'
            if 'name = "pytorch"' not in content:
                # Find the [tool.poetry.dependencies] section and add source right before it
                deps_match = re.search(r'(\[tool\.poetry\.dependencies\])', content)
                if deps_match:
                    insert_pos = deps_match.start()
                    # Find the start of the line to insert before the dependencies section
                    # Look backwards for a newline to insert on a new line
                    line_start = content.rfind('\n', 0, insert_pos) + 1
                    # Insert with proper spacing
                    content = content[:line_start] + pytorch_source + '\n\n' + content[line_start:]
                    print("   ✅ Added PyTorch source URL to pyproject.toml (explicit priority)")
                else:
                    # Fallback: append at the end of [tool.poetry] section
                    # Find the last field in [tool.poetry] section (before any [tool.poetry.*] subsections)
                    poetry_deps_match = re.search(r'(\[tool\.poetry\.)', content)
                    if poetry_deps_match:
                        insert_pos = poetry_deps_match.start()
                        # Find the previous newline
                        line_start = content.rfind('\n', 0, insert_pos) + 1
                        content = content[:line_start] + pytorch_source + '\n\n' + content[line_start:]
                        print("   ✅ Added PyTorch source URL to pyproject.toml (explicit priority)")
            
            # Update torch and torchvision to explicitly use the pytorch source
            # Format: torch = {version = "2.7.1", source = "pytorch"}
            torch_pattern = r'torch = "([^"]+)"'
            if re.search(torch_pattern, content):
                torch_match = re.search(torch_pattern, content)
                if torch_match:
                    torch_version = torch_match.group(1)
                    content = re.sub(torch_pattern, f'torch = {{version = "{torch_version}", source = "pytorch"}}', content)
                    print("   ✅ Configured torch to use PyTorch source")
            
            torchvision_pattern = r'torchvision = "([^"]+)"'
            if re.search(torchvision_pattern, content):
                torchvision_match = re.search(torchvision_pattern, content)
                if torchvision_match:
                    torchvision_version = torchvision_match.group(1)
                    content = re.sub(torchvision_pattern, f'torchvision = {{version = "{torchvision_version}", source = "pytorch"}}', content)
                    print("   ✅ Configured torchvision to use PyTorch source")
            
            # Make file writable before writing
            pyproject_path.chmod(0o644)
            with open(pyproject_path, 'w') as f:
                f.write(content)
            if re.search(old_comment, content) or 'name = "pytorch"' not in content:
                print("   ✅ Updated pyproject.toml")
            else:
                print("   ✅ Made pyproject.toml writable")
        except Exception as e:
            print(f"   ⚠️  Warning: Could not update pyproject.toml: {e}")
    
    # Make all generated files writable
    print("   Setting file permissions...")
    generated_files = [
        "dvc.yaml", "dvc-release.yaml", "params.yaml", ".env.example",
        "Dockerfile", ".dvc/config", ".circleci/config.yml"
    ]
    
    for file_path in generated_files:
        target = project_dir / file_path
        if target.exists():
            try:
                target.chmod(0o644)  # rw-r--r--
            except Exception as e:
                print(f"   ⚠️  Could not set permissions for {file_path}: {e}")
    
    # Make all Python source files writable (recursively)
    src_dir = project_dir / "src"
    if src_dir.exists():
        try:
            for py_file in src_dir.rglob("*.py"):
                py_file.chmod(0o644)
            print("   ✅ Made all Python source files writable")
        except Exception as e:
            print(f"   ⚠️  Warning: Could not set permissions for Python files: {e}")

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
