from os import environ

from dagster_wandb import wandb_artifacts_io_manager, wandb_resource

from dagster import (
    load_assets_from_package_module,
    make_values_resource,
    repository,
    with_resources,
)

from . import assets
from .ops.launch.run_launch_agent import run_launch_agent_example
from .ops.launch.run_launch_job import run_launch_job_example
from .ops.partitioned_job import partitioned_job_example
from .ops.simple_job import simple_job_example


@repository
def dagster_with_wandb():
    return [
        simple_job_example,
        partitioned_job_example,
        run_launch_agent_example,
        run_launch_job_example,
        *with_resources(
            load_assets_from_package_module(assets),
            resource_defs={
                "wandb_config": make_values_resource(
                    entity=str,
                    project=str,
                ),
                "wandb_resource": wandb_resource.configured(
                    {"api_key": {"env": "WANDB_API_KEY"}}
                ),
                "io_manager": wandb_artifacts_io_manager.configured(
                    {"cache_duration_in_minutes": 60}
                ),
            },
            resource_config_by_key={
                "wandb_config": {
                    "config": {
                        "entity": environ["WANDB_ENTITY"],
                        "project": environ["WANDB_PROJECT"],
                    }
                }
            },
        ),
    ]
