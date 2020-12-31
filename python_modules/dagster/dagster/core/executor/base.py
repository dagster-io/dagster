import abc


class Executor(abc.ABC):  # pylint: disable=no-init
    @abc.abstractmethod
    def execute(self, pipeline_context, execution_plan):
        """
        For the given context and execution plan, orchestrate a series of sub plan executions in a way that satisfies the whole plan being executed.

        Args:
            pipeline_context (SystemPipelineExecutionContext): The pipeline execution context.
            execution_plan (ExecutionPlan): The plan to execute.

        Returns:
            A stream of dagster events.
        """

    @abc.abstractproperty
    def retries(self):
        """
        The Retries state / policy for this instance of the Executor. Executors should allow this to be
        controlled via configuration if possible.

        Returns: Retries
        """
