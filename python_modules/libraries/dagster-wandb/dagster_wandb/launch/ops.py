from dagster import OpExecutionContext, op
from wandb.sdk.launch import launch, launch_add

from dagster_wandb.launch.configs import launch_agent_config, launch_config


def raise_on_invalid_config(context: OpExecutionContext):
    entity = context.resources.wandb_config["entity"]
    if entity == "":
        raise RuntimeError(
            "(dagster_wandb) An empty string was provided for the 'entity' property of the"
            " 'wandb_config'."
        )

    project = context.resources.wandb_config["project"]
    if project == "":
        raise RuntimeError(
            "(dagster_wandb) An empty string was provided for the 'project' property of the"
            " 'wandb_config'."
        )


@op(
    required_resource_keys={"wandb_resource", "wandb_config"},
    config_schema=launch_agent_config(),
)
def run_launch_agent(context: OpExecutionContext):
    """It starts a Launch Agent and runs it as a long running process until stopped manually.

    Agents are processes that poll launch queues and execute the jobs (or dispatch them to external
    services to be executed) in order.

    **Example:**

    .. code-block:: YAML

        # config.yaml

        resources:
          wandb_config:
            config:
              entity: my_entity
              project: my_project
        ops:
          run_launch_agent:
            config:
              max_jobs: -1
              queues:
                - my_dagster_queue

    .. code-block:: python

        from dagster_wandb.launch.ops import run_launch_agent
        from dagster_wandb.resources import wandb_resource

        from dagster import job, make_values_resource


        @job(
            resource_defs={
                "wandb_config": make_values_resource(
                    entity=str,
                    project=str,
                ),
                "wandb_resource": wandb_resource.configured(
                    {"api_key": {"env": "WANDB_API_KEY"}}
                ),
            },
        )
        def run_launch_agent_example():
            run_launch_agent()

    """
    raise_on_invalid_config(context)
    config = {
        "entity": context.resources.wandb_config["entity"],
        "project": context.resources.wandb_config["project"],
        **context.op_config,
    }
    context.log.info(f"Launch agent configuration: {config}")
    context.log.info("Running Launch agent...")
    launch.create_and_run_agent(api=context.resources.wandb_resource["api"], config=config)  # pyright: ignore[reportFunctionMemberAccess]


@op(
    required_resource_keys={
        "wandb_resource",
        "wandb_config",
    },
    config_schema=launch_config(),
)
def run_launch_job(context: OpExecutionContext):
    """Executes a Launch job.

    A Launch job is assigned to a queue in order to be executed. You can create a queue or use the
    default one. Make sure you have an active agent listening to that queue. You can run an agent
    inside your Dagster instance but can also consider using a deployable agent in Kubernetes.

    **Example:**

    .. code-block:: YAML

        # config.yaml

        resources:
          wandb_config:
            config:
              entity: my_entity
              project: my_project
        ops:
          my_launched_job:
            config:
              entry_point:
                - python
                - train.py
              queue: my_dagster_queue
              uri: https://github.com/wandb/example-dagster-integration-with-launch

    .. code-block:: python

            from dagster_wandb.launch.ops import run_launch_job
            from dagster_wandb.resources import wandb_resource

            from dagster import job, make_values_resource


            @job(
                resource_defs={
                    "wandb_config": make_values_resource(
                        entity=str,
                        project=str,
                    ),
                    "wandb_resource": wandb_resource.configured(
                        {"api_key": {"env": "WANDB_API_KEY"}}
                    ),
                },
            )
            def run_launch_job_example():
                run_launch_job.alias("my_launched_job")() # we rename the job with an alias

    """
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
        launch.run(api=context.resources.wandb_resource["api"], config=config)  # pyright: ignore[reportFunctionMemberAccess]
    else:
        synchronous = config.get("synchronous", True)
        config.pop("synchronous", None)
        queued_run = launch_add(**config)
        if synchronous is True:
            context.log.info(
                f"Synchronous Launch job added to queue with name={queue}. Waiting for"
                " completion..."
            )
            queued_run.wait_until_finished()
        else:
            context.log.info(f"Asynchronous Launch job added to queue with name={queue}")
