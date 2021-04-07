import abc

from dagster.core.execution.retries import RetryMode


class Executor(abc.ABC):  # pylint: disable=no-init
    @abc.abstractmethod
    def execute(self, pipeline_context, execution_plan):
        """
        For the given context and execution plan, orchestrate a series of sub plan executions in a way that satisfies the whole plan being executed.

        Args:
            pipeline_context (PlanOrchestrationContext): The pipeline orchestration context.
            execution_plan (ExecutionPlan): The plan to execute.

        Returns:
            A stream of dagster events.
        """

    @abc.abstractproperty
    def retries(self) -> RetryMode:
        """
        Whether retries are enabled or disabled for this instance of the executor.

        Executors should allow this to be controlled via configuration if possible.

        Returns: RetryMode
        """
