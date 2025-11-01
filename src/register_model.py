
import argparse
import os
import mlflow
from mlflow.tracking import MlflowClient

def register_model(run_id: str, tag: str):
    """
    Registers the model artifact from a given run ID to the MLflow Model Registry
    and optionally sets a version tag (e.g., 'ProductionCandidate').
    """
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI"))
    client = MlflowClient()
    
    model_name = os.getenv("MLFLOW_MODEL_NAME", "default-model")
    model_uri = f"runs:/{run_id}/model"

    print(f"Registering model from run {run_id} as '{model_name}'...")
    
    try:
        # 1. Register the model from the run artifacts
        model_version = mlflow.register_model(
            model_uri=model_uri,
            name=model_name
        )
        version = model_version.version
        print(f"✅ Successfully registered model version: {version}")

        # 2. Transition the version stage (e.g., to Staging)
        if tag:
            client.transition_model_version_stage(
                name=model_name,
                version=version,
                stage="Staging" # Use 'Staging' as a universal "ready for review" tag
            )
            print(f"✅ Model version {version} transitioned to stage: Staging")

        # 3. Add a custom tag for easy identification
        client.set_model_version_tag(
            name=model_name,
            version=version,
            key="deployment_status",
            value=tag # e.g., 'production-candidate'
        )
        print(f"✅ Model version {version} tagged with 'deployment_status': '{tag}'")

    except Exception as e:
        print(f"❌ Error during model registration: {e}")
        # Optionally, fail the CI pipeline here

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Register model in MLflow.")
    parser.add_argument(
        '--run-id', 
        required=True, 
        help='The MLflow Run ID containing the model artifact.'
    )
    parser.add_argument(
        '--tag', 
        default='candidate', 
        help='Custom tag to mark the model version (e.g., production-candidate).'
    )
    args = parser.parse_args()
    register_model(args.run_id, args.tag)