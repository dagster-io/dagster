from dagster._core.libraries import DagsterLibraryRegistry

from .io_manager import WandbArtifactsIOManagerError, wandb_artifacts_io_manager
from .launch.ops import run_launch_agent, run_launch_job
from .resources import wandb_resource
from .types import SerializationModule, WandbArtifactConfiguration
from .version import __version__

DagsterLibraryRegistry.register("dagster-wandb", __version__)

__all__ = [
    "WandbArtifactsIOManagerError",
    "SerializationModule",
    "wandb_resource",
    "wandb_artifacts_io_manager",
    "WandbArtifactConfiguration",
    "run_launch_agent",
    "run_launch_job",
]
