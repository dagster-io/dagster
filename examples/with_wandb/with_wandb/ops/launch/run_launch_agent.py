from dagster import job, make_values_resource
from dagster_wandb.launch.ops import run_launch_agent
from dagster_wandb.resources import wandb_resource


@job(
    resource_defs={
        "wandb_config": make_values_resource(
            entity=str,
            project=str,
        ),
        "wandb_resource": wandb_resource.configured({"api_key": {"env": "WANDB_API_KEY"}}),
    },
)
def run_launch_agent_example():
    """Example of a simple job that runs a W&B Launch agent.

    The Launch agent will run until stopped.

    Check the content of the config.yaml file to view the provided config.

    Agents are processes that poll Launch queues and execute the jobs (or dispatch them to external
    services to be executed) in order.

    Reference: https://docs.wandb.ai/guides/launch/agents
    """
    run_launch_agent()
