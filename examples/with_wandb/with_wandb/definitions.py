from dagster import Definitions, StringSource, load_assets_from_package_module, make_values_resource
from dagster_wandb import wandb_artifacts_io_manager, wandb_resource

from . import assets
from .ops.launch.run_launch_agent import run_launch_agent_example
from .ops.launch.run_launch_job import run_launch_job_example
from .ops.partitioned_job import partitioned_job_example
from .ops.simple_job import simple_job_example

wandb_config = make_values_resource(
    entity=StringSource,
    project=StringSource,
)

defs = Definitions(
    assets=load_assets_from_package_module(assets),
    jobs=[
        simple_job_example,
        partitioned_job_example,
        run_launch_agent_example,
        run_launch_job_example,
    ],
    resources={
        "wandb_config": wandb_config.configured(
            {
                "entity": {"env": "WANDB_ENTITY"},
                "project": {"env": "WANDB_PROJECT"},
            }
        ),
        "wandb_resource": wandb_resource.configured({"api_key": {"env": "WANDB_API_KEY"}}),
        "io_manager": wandb_artifacts_io_manager.configured({"cache_duration_in_minutes": 60}),
    },
)
