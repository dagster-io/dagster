import io
import os
import pickle
from abc import ABC, abstractmethod
from typing import Any

import boto3
import dagster as dg
import torch


# start_model_storage_interface
class ModelStoreResource(dg.ConfigurableResource, ABC):
    """Abstract base class for model storage resources."""

    @abstractmethod
    def save_model(self, model_data: dict[str, Any], model_name: str):
        pass

    @abstractmethod
    def load_model(self, model_name: str) -> dict[str, Any]:
        pass

    @abstractmethod
    def list_models(self) -> list[str]:
        """List available models, sorted by modification time (newest first)."""
        pass


# end_model_storage_interface


class LocalModelStoreResource(ModelStoreResource):
    """Local file system model storage."""

    models_path: str = "./models"

    def save_model(self, model_data: dict[str, Any], model_name: str):
        """Save model data to local filesystem."""
        os.makedirs(self.models_path, exist_ok=True)
        model_path = os.path.join(self.models_path, f"{model_name}.pkl")

        with open(model_path, "wb") as f:
            pickle.dump(model_data, f)

    def load_model(self, model_name: str) -> dict[str, Any]:
        """Load model data from local filesystem."""
        model_path = os.path.join(self.models_path, f"{model_name}.pkl")
        with open(model_path, "rb") as f:
            return pickle.load(f)

    def list_models(self) -> list[str]:
        """List available models, sorted by modification time (newest first)."""
        if not os.path.exists(self.models_path):
            return []

        model_files = [f for f in os.listdir(self.models_path) if f.endswith(".pkl")]
        # Sort by modification time, newest first
        model_files.sort(
            key=lambda x: os.path.getmtime(os.path.join(self.models_path, x)),
            reverse=True,
        )

        # Return just the model names without extension
        return [os.path.splitext(f)[0] for f in model_files]


class S3ModelStoreResource(ModelStoreResource):
    """S3-based model storage for production."""

    bucket_name: str
    models_prefix: str = "models/"

    def save_model(self, model, model_name: str):
        # Create a buffer to store the model
        buffer = io.BytesIO()
        torch.save(model.state_dict(), buffer)
        buffer.seek(0)

        # Generate the S3 key for the model
        s3_key = os.path.join(self.models_prefix, f"{model_name}.pth")

        # Upload to S3
        s3_client = boto3.client("s3")
        s3_client.upload_fileobj(buffer, self.bucket_name, s3_key)

    def load_model(self, model_name: str):
        # Create a buffer to receive the model data
        buffer = io.BytesIO()

        # Generate the S3 key for the model
        s3_key = os.path.join(self.models_prefix, f"{model_name}.pth")

        # Download from S3
        s3_client = boto3.client("s3")
        s3_client.download_fileobj(self.bucket_name, s3_key, buffer)

        # Reset buffer position and load the model
        buffer.seek(0)
        return torch.load(buffer)

    def list_models(self) -> list[str]:
        """List available models from S3, sorted by modification time (newest first)."""
        s3_client = boto3.client("s3")

        try:
            # List objects with the models prefix
            response = s3_client.list_objects_v2(Bucket=self.bucket_name, Prefix=self.models_prefix)

            if "Contents" not in response:
                return []

            # Get model files and their last modified times
            model_objects = []
            for obj in response["Contents"]:
                if obj["Key"].endswith(".pth"):
                    model_objects.append({"key": obj["Key"], "last_modified": obj["LastModified"]})

            # Sort by modification time, newest first
            model_objects.sort(key=lambda x: x["last_modified"], reverse=True)

            # Return just the model names without extension and prefix
            return [os.path.splitext(os.path.basename(obj["key"]))[0] for obj in model_objects]

        except Exception:
            # Log error and return empty list
            return []


class ComputeResource(dg.ConfigurableResource):
    """Compute configuration resource for ML training and inference.

    This resource supports both local compute and AWS compute configurations.
    For local compute, it manages device selection and batch processing.
    For AWS compute, it provides SageMaker configuration and instance management.
    """

    # Compute environment
    compute_env: str = "local"  # Options: "local", "sagemaker"
    region: str = "us-east-1"  # AWS region for SageMaker

    # Local compute settings
    device: str = "cpu"  # Options: "cpu", "cuda", "mps"
    batch_size: int = 32
    max_workers: int = 4

    # SageMaker settings
    instance_type: str = "ml.m5.xlarge"  # Default SageMaker instance
    instance_count: int = 1

    def get_training_config(self):
        """Get compute configuration for model training."""
        if self.compute_env == "local":
            # Validate and set device
            if self.device == "cuda" and not torch.cuda.is_available():
                self.device = "cpu"
            elif self.device == "mps" and not torch.backends.mps.is_available():
                self.device = "cpu"

            return {
                "device": self.device,
                "batch_size": self.batch_size,
                "max_workers": self.max_workers,
            }

        elif self.compute_env == "sagemaker":
            return {
                "instance_type": self.instance_type,
                "instance_count": self.instance_count,
                "region": self.region,
                "framework": "pytorch",
                "py_version": "py39",
                "batch_size": self.batch_size,
            }

        else:
            raise ValueError(f"Unsupported compute environment: {self.compute_env}")

    def get_inference_config(self):
        """Get compute configuration for model inference."""
        if self.compute_env == "local":
            return self.get_training_config()

        elif self.compute_env == "sagemaker":
            return {
                "instance_type": "ml.t2.medium",  # Default to smaller instance for inference
                "instance_count": 1,
                "region": self.region,
                "framework": "pytorch",
                "py_version": "py39",
                "batch_size": self.batch_size,
            }

    def cleanup(self):
        """Cleanup compute resources if necessary."""
        if self.compute_env == "sagemaker":
            # Add cleanup logic for SageMaker endpoints or training jobs if needed
            pass


local_model_storage = LocalModelStoreResource(models_path="./models")
compute_config = ComputeResource(device="cpu", batch_size=32, max_workers=4)


@dg.definitions
def resources():
    return dg.Definitions(
        resources={
            "model_storage": local_model_storage,
            "compute": compute_config,
        }
    )
