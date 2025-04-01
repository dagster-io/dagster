from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_wandb.io_manager import WandbArtifactsIOManagerError, wandb_artifacts_io_manager
from dagster_wandb.launch.ops import run_launch_agent, run_launch_job
from dagster_wandb.resources import wandb_resource
from dagster_wandb.types import SerializationModule, WandbArtifactConfiguration
from dagster_wandb.version import __version__

DagsterLibraryRegistry.register("dagster-wandb", __version__)

__all__ = [
    "SerializationModule",
    "WandbArtifactConfiguration",
    "WandbArtifactsIOManagerError",
    "run_launch_agent",
    "run_launch_job",
    "wandb_artifacts_io_manager",
    "wandb_resource",
]
