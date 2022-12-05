from wandb.sdk.launch import launch
from wandb.sdk.launch.launch_add import launch_add

from dagster import OpExecutionContext, op

from .configs import launch_agent_config, launch_config


def raise_on_invalid_config(context: OpExecutionContext):
    entity = context.resources.wandb_config["entity"]
    if entity == "":
        raise RuntimeError(
            "(dagster_wandb) An empty string was provided for the 'entity' property of the 'wandb_config'."
        )

    project = context.resources.wandb_config["project"]
    if project == "":
        raise RuntimeError(
            "(dagster_wandb) An empty string was provided for the 'project' property of the 'wandb_config'."
        )


@op(
    required_resource_keys={"wandb_resource", "wandb_config"},
    config_schema=launch_agent_config(),
)
def run_launch_agent(context: OpExecutionContext):
    raise_on_invalid_config(context)
    config = {
        "entity": context.resources.wandb_config["entity"],
        "project": context.resources.wandb_config["project"],
        **context.op_config,
    }
    context.log.info(f"Launch agent configuration: {config}")
    context.log.info("Running Launch agent...")
    launch.create_and_run_agent(api=context.resources.wandb_resource["api"], config=config)


@op(
    required_resource_keys={
        "wandb_resource",
        "wandb_config",
    },
    config_schema=launch_config(),
)
def run_launch_job(context: OpExecutionContext):
    raise_on_invalid_config(context)
    config = {
        "entity": context.resources.wandb_config["entity"],
        "project": context.resources.wandb_config["project"],
        **context.op_config,
    }
    context.log.info(f"Launch job configuration: {config}")

    queue = context.op_config.get("queue")
    if queue is None:
        context.log.info("No queue provided, running Launch job locally")
        launch.run(api=context.resources.wandb_resource["api"], config=config)
    else:
        synchronous = config.get("synchronous", True)
        config.pop("synchronous", None)
        queued_run = launch_add(**config)
        if synchronous is True:
            context.log.info(
                f"Synchronous Launch job added to queue with name={queue}. Waiting for completion..."
            )
            queued_run.wait_until_finished()
        else:
            context.log.info(f"Asynchronous Launch job added to queue with name={queue}")
