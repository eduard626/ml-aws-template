#!/usr/bin/env python3
"""
bootstrap.py
=============
Bootstraps a new ML project from the projen-based ML AWS template.

Usage:
  python3 bootstrap.py --name my-new-project

Requirements (must be on PATH):
  - python3
  - git
  - npm (with npx)
  - docker
  - poetry
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path

# --- Configuration ---
SEED_REPO_URL = "https://github.com/eduard626/ml-aws-template.git"

PROJEN_GENERATED_FILES = [
    # Node / Projen
    "package.json",
    "package-lock.json",

    # Poetry-managed
    "pyproject.toml",
    "poetry.lock",

    # Git & env files
    ".gitattributes",
    ".gitignore",
    ".env.example",

    # Config & pipelines
    "dvc.yaml",
    "params.yaml",
    "Dockerfile",
    ".circleci/config.yml",
]
# ----------------------


def run_command(command, cwd=None, env=None, shell=False, quiet=False):
    """Run a shell command and exit on failure."""
    cmd_display = " ".join(command)
    if not quiet:
        print(f"\n🚀 Running: {cmd_display}")
    try:
        subprocess.run(
            command,
            cwd=cwd,
            env=env,
            check=True,
            shell=shell,
            stdout=None if not quiet else subprocess.DEVNULL,
            stderr=None if not quiet else subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        print(f"\n❌ Command failed: {cmd_display}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"\n❌ Command not found: {command[0]}")
        sys.exit(1)


def get_git_config(key, default="unknown"):
    """Get a global Git config value safely."""
    try:
        result = subprocess.run(
            ["git", "config", "--global", key],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip() or default
    except subprocess.CalledProcessError:
        print(f"⚠️  Git config for '{key}' not found, using default '{default}'")
        return default


def purge_generated_files(project_dir):
    """Remove files that Projen will re-generate, including nested paths."""
    print("🧹 Cleaning up pre-generated files...")
    for filename in PROJEN_GENERATED_FILES:
        filepath = project_dir / filename
        if filepath.exists():
            if filepath.is_file():
                print(f"   -> Deleting file: {filename}")
                filepath.unlink()
            elif filepath.is_dir():
                print(f"   -> Removing directory: {filename}")
                shutil.rmtree(filepath)
        else:
            # Force removal for hidden files like .gitattributes
            print(f"   -> File not found: {filename}, skipping (but checking hidden files)")



def check_prereqs():
    """Ensure all required tools are installed."""
    for tool in ["git", "npm", "npx", "docker", "poetry"]:
        if shutil.which(tool) is None:
            print(f"\n❌ Required tool '{tool}' not found on PATH.")
            sys.exit(1)
    print("✅ All required tools found.")


def main():
    parser = argparse.ArgumentParser(description="Bootstrap a new ML project from the template.")
    parser.add_argument("-n", "--name", required=True, help="New project name (e.g., customer-churn-model)")
    args = parser.parse_args()

    project_name = args.name.strip()
    module_name = project_name.replace("-", "_")
    project_dir = Path(project_name).resolve()

    if project_dir.exists():
        print(f"❌ Error: Directory '{project_name}' already exists.")
        sys.exit(1)

    print(f"--- Bootstrapping new ML project: {project_name} ---")
    check_prereqs()

    # 1. Clone the seed repo
    run_command(["git", "clone", SEED_REPO_URL, project_name])

    # 2. Remove template git history
    git_dir = project_dir / ".git"
    if git_dir.exists():
        print("🧹 Removing template Git history...")
        shutil.rmtree(git_dir)

    # 3. Clean up Projen-generated files
    purge_generated_files(project_dir)

    # 4. Prepare environment for Projen
    env = os.environ.copy()
    env["PROJECT_NAME"] = project_name
    env["MODULE_NAME"] = module_name
    env["AUTHOR_NAME"] = get_git_config("user.name", "ML Developer")
    env["AUTHOR_MAIL"] = get_git_config("user.email", "ml@example.com")

    # Ensure .gitattributes is gone
    gitattributes_path = project_dir / ".gitattributes"
    if gitattributes_path.exists():
        print("🗑️ Removing pre-existing .gitattributes")
        gitattributes_path.unlink()


    print("📂 Files in project dir before Projen synthesis:")
    for f in project_dir.iterdir():
        print("  ", f.name)

    # 5. Run Projen synthesis
    print("\n🔨 Running Projen synthesis...")
    run_command(["npx", "projen"], cwd=project_dir, env=env)

    # 6. Install Node dependencies
    print("\n📦 Installing Node dependencies...")
    run_command(["npm", "install"], cwd=project_dir, env=env)

    # 7. Install Python dependencies
    print("\n🐍 Installing Poetry dependencies (including dev + s3_storage)...")
    run_command([
        "poetry",
        "install",
        "--with", "dev",
        "--with", "s3_storage"
    ], cwd=project_dir, env=env)

    # 8. Append DVC filters to .gitattributes
    gitattributes_file = project_dir / ".gitattributes"
    dvc_line = "*.dvc filter=lfs diff=lfs merge=lfs -text\n"

    if gitattributes_file.exists():
        print("📝 Appending DVC filters to existing .gitattributes")
        with open(gitattributes_file, "a") as f:
            f.write(dvc_line)
    else:
        print("📝 Creating new .gitattributes with DVC filters")
        with open(gitattributes_file, "w") as f:
            f.write(dvc_line)

    # 9. Initialize DVC and Git
    print("\n🧠 Initializing DVC...")
    run_command(["poetry", "run", "dvc", "init", "--no-scm"], cwd=project_dir, env=env)

    print("\n🔧 Initializing new Git repo...")
    run_command(["git", "init"], cwd=project_dir)
    run_command(["git", "config", "user.name", env["AUTHOR_NAME"]], cwd=project_dir)
    run_command(["git", "config", "user.email", env["AUTHOR_MAIL"]], cwd=project_dir)
    run_command(["git", "add", "."], cwd=project_dir)
    run_command(["git", "commit", "-m", "Initial project bootstrap (via template)"], cwd=project_dir)

    # 10. Summary
    print("\n🎉 Success! Your new ML project is ready.")
    print("\nNext steps:")
    print(f"  1. cd {project_name}")
    print("  2. poetry shell")
    print("  3. git remote add origin https://github.com/your-org/{project_name}.git")
    print("  4. git push -u origin main")
    print("  5. dvc remote add -d my_remote s3://your-bucket/dvc-storage")
    print("  6. Start coding 🚀")


if __name__ == "__main__":
    main()
