from collections import namedtuple

from dagster import check
from dagster.core.definitions import ExecutorDefinition, IPipeline
from dagster.core.instance import DagsterInstance


class InitExecutorContext(
    namedtuple(
        "InitExecutorContext",
        "pipeline executor_def executor_config instance",
    )
):
    """Executor-specific initialization context.

    Attributes:
        pipeline (IPipeline): The pipeline to be executed.
        executor_def (ExecutorDefinition): The definition of the executor currently being
            constructed.
        executor_config (dict): The parsed config passed to the executor.
        instance (DagsterInstance): The current instance.
    """

    def __new__(
        cls,
        pipeline,
        executor_def,
        executor_config,
        instance,
    ):
        return super(InitExecutorContext, cls).__new__(
            cls,
            pipeline=check.inst_param(pipeline, "pipeline", IPipeline),
            executor_def=check.inst_param(executor_def, "executor_def", ExecutorDefinition),
            executor_config=check.dict_param(executor_config, executor_config, key_type=str),
            instance=check.inst_param(instance, "instance", DagsterInstance),
        )
