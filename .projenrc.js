
const { python, TextFile, SampleFile } = require('projen');

const fs = require('fs'); // Node's filesystem module to read external files
const path = require('path'); // Node's path module

// Helper function to read external template files
function readTemplate(filename, replacements = {}, asString = false) {
  let content = fs.readFileSync(path.join('template_configs', filename), 'utf8');
  for (const [key, value] of Object.entries(replacements)) {
    content = content.replace(new RegExp(`{{ ${key} }}`, 'g'), value);
  }
  return asString ? content : content.split('\n');
}

const project = new python.PythonProject({
  authorName: process.env.AUTHOR_NAME || 'My Name',
  authorEmail: process.env.AUTHOR_MAIL | 'my-email@email.com',
  moduleName: process.env.MODULE_NAME || 'my_ml_project',
  name: process.env.PROJECT_NAME || 'my-ml-project',
  version: '0.1.0',
  
  // Poetry automatically handles dependencies via 'addDependency'
  // Note: DVC[s3] is specified as 'dvc', and the extras are handled by the library
  deps: [
    'pytorch-lightning',
    'torch',
    'torchvision',
    'torchmetrics',
    'mlflow',
    'dvc', // Core DVC package
    'boto3',
    'matplotlib',
    'numpy',
    'tqdm',
    'onnx',
    'onnxruntime-gpu',
    'python-dotenv',
    'gitpython',
  ],

  poetry: {
    // Add DVC[s3] as a dependency group
    optionalDependencies: {
      s3_storage: ['dvc[s3]'],
    },
    // Add a development group for dev dependencies
    dev: {
      dependencies: {
        pytest: '^7.0.0',
        'pytest-cov': '^4.0.0',
        // Add tools like black, isort here if needed
      }
    }
  },

  // Projen tasks to integrate DVC
  tasks: {
    'dvc:pull': { exec: 'dvc pull' },
    'dvc:push': { exec: 'dvc push' },
    'dvc:repro': { exec: 'dvc repro' },
  },

  // Files to gitignore
  gitignore: [
    'data/',
    'models/',
    'notebooks/',
    'mlruns/',
    '.dvc/cache',
    '*.DS_Store',
    '.env',
  ],
});

// --- Scaffolding Essential Config Files ---

const moduleName = project.moduleName; // Convenience variable

console.log('Existing files:', project.files.map(f => f.path));
const github = new projen.github.GitHub(project, { ... projen.github.GitHubOptions });

console.log("Before custom .gitattributes logic, project.files includes:", project.files.map(f => f.path));

// project.gitAttributes.addAttributes('*.dvc filter=lfs diff=lfs merge=lfs -text');

// DVC: Main pipeline definition
new TextFile(project, 'dvc.yaml', {
  lines: readTemplate('template_configs/dvc.yaml', { moduleName }, true),
});

// DVC/MLflow: Parameters file
new TextFile(project, 'params.yaml', {
  lines: readTemplate('template_configs/params.yaml', {}, true),
});

// Example .env file for local development
new TextFile(project, '.env.example', {
  lines: readTemplate('template_configs/environment.env', {}, true),
});

// --- CircleCI: AWS-Aware CI/CD Pipeline ---
new TextFile(project, '.circleci/config.yml', {
  lines: readTemplate('template_configs/circleci_config.yml', { projectName: project.name, moduleName }, true),
});

// --- Dockerfile ---
new TextFile(project, 'Dockerfile', {
  lines: readTemplate('template_configs/Dockerfile', { moduleName }, true),
});

// --- 3. SCAFFOLDING PYTHON SOURCE CODE (RECIPES) ---

// Base module and __init__ files
new SampleFile(project, `src/${moduleName}/__init__.py`, { contents: '' });
new SampleFile(project, `src/${moduleName}/data/__init__.py`, { contents: '' });
new SampleFile(project, `src/${moduleName}/model/__init__.py`, { contents: '' });

// Add placeholders for other key modules
new SampleFile(project, `src/${project.moduleName}/model/model.py`, {
  contents: readTemplate('src/model/model.py', { moduleName }, true),
});
new SampleFile(project, `src/${project.moduleName}/data/datamodule.py`, {
  contents: readTemplate('src/data/datamodule.py', { moduleName }, true),
});

new SampleFile(project, `src/${moduleName}/register_model.py`, {
  contents: readTemplate('src/register_model.py', { moduleName }, true), // Uses external file
});

new SampleFile(project, `src/${moduleName}/data/preprocess.py`, {
  contents: readTemplate('src/data/preprocess.py', { moduleName }, true), // Uses external file
});

new SampleFile(project, `src/${moduleName}/train.py`, {
  contents: readTemplate('src/train.py', { moduleName }, true), // Uses external file for cleaner code
});


new SampleFile(project, `src/${moduleName}/export_and_benchmark.py`, {
  contents: readTemplate('src/export_and_benchmark.py', { moduleName }, true), // Uses external file
});

// Add placeholder for a simple test
new SampleFile(project, `tests/test_basic.py`, {
  contents: `
def test_import():
    import ${project.moduleName}
    assert 1 == 1
`,
});


// Synthesize the project
project.synth();