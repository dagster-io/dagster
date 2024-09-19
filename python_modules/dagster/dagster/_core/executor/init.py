from typing import Mapping, NamedTuple

import dagster._check as check
from dagster._annotations import PublicAttr
from dagster._core.definitions import ExecutorDefinition, IJob
from dagster._core.instance import DagsterInstance


class InitExecutorContext(
    NamedTuple(
        "InitExecutorContext",
        [
            ("job", PublicAttr[IJob]),
            ("executor_def", PublicAttr[ExecutorDefinition]),
            ("executor_config", PublicAttr[Mapping[str, object]]),
            ("instance", PublicAttr[DagsterInstance]),
        ],
    )
):
    """Executor-specific initialization context.

    Attributes:
        job (IJob): The job to be executed.
        executor_def (ExecutorDefinition): The definition of the executor currently being
            constructed.
        executor_config (dict): The parsed config passed to the executor.
        instance (DagsterInstance): The current instance.
    """

    def __new__(
        cls,
        job: IJob,
        executor_def: ExecutorDefinition,
        executor_config: Mapping[str, object],
        instance: DagsterInstance,
    ):
        return super(InitExecutorContext, cls).__new__(
            cls,
            job=check.inst_param(job, "job", IJob),
            executor_def=check.inst_param(executor_def, "executor_def", ExecutorDefinition),
            executor_config=check.mapping_param(executor_config, "executor_config", key_type=str),
            instance=check.inst_param(instance, "instance", DagsterInstance),
        )
