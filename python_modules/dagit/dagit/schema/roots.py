from dagit.schema import dauphin
from dagit.schema import model
from ..version import __version__
from dagster.core.execution import ExecutionSelector


class DauphinQuery(dauphin.ObjectType):
    class Meta:
        name = "Query"

    version = dauphin.NonNull(dauphin.String)
    pipelineOrError = dauphin.Field(
        dauphin.NonNull("PipelineOrError"), params=dauphin.NonNull("ExecutionSelector")
    )
    pipeline = dauphin.Field(
        dauphin.NonNull("Pipeline"), params=dauphin.NonNull("ExecutionSelector")
    )
    pipelinesOrError = dauphin.NonNull("PipelinesOrError")
    pipelines = dauphin.Field(dauphin.NonNull("PipelineConnection"))

    type = dauphin.Field(
        "Type",
        pipelineName=dauphin.NonNull(dauphin.String),
        typeName=dauphin.Argument(dauphin.NonNull(dauphin.String)),
    )

    pipelineRuns = dauphin.non_null_list("PipelineRun")
    pipelineRun = dauphin.Field("PipelineRun", runId=dauphin.NonNull(dauphin.ID))

    isPipelineConfigValid = dauphin.Field(
        dauphin.NonNull("PipelineConfigValidationResult"),
        args={
            "pipeline": dauphin.Argument(dauphin.NonNull("ExecutionSelector")),
            "config": dauphin.Argument("PipelineConfig"),
        },
    )

    executionPlan = dauphin.Field(
        dauphin.NonNull("ExecutionPlanResult"),
        args={
            "pipeline": dauphin.Argument(dauphin.NonNull("ExecutionSelector")),
            "config": dauphin.Argument("PipelineConfig"),
        },
    )

    def resolve_version(self, _info):
        return __version__

    def resolve_pipelineOrError(self, info, **kwargs):
        return model.get_pipeline(info, kwargs["params"].to_selector())

    def resolve_pipeline(self, info, **kwargs):
        return model.get_pipeline_or_raise(info, kwargs["params"].to_selector())

    def resolve_pipelinesOrError(self, info):
        return model.get_pipelines(info)

    def resolve_pipelines(self, info):
        return model.get_pipelines_or_raise(info)

    def resolve_type(self, info, pipelineName, typeName):
        return model.get_pipeline_type(info, pipelineName, typeName)

    def resolve_pipelineRuns(self, info):
        return model.get_runs(info)

    def resolve_pipelineRun(self, info, runId):
        return model.get_run(info, runId)

    def resolve_isPipelineConfigValid(self, info, pipeline, config):
        return model.validate_pipeline_config(info, pipeline.to_selector(), config)

    def resolve_executionPlan(self, info, pipeline, config):
        return model.get_execution_plan(info, pipeline.to_selector(), config)


class StartPipelineExecutionMutation(dauphin.Mutation):
    class Meta:
        name = "StartPipelineExecutionMutation"

    class Arguments:
        pipeline = dauphin.NonNull("ExecutionSelector")
        config = dauphin.Argument("PipelineConfig")

    Output = dauphin.NonNull("StartPipelineExecutionResult")

    def mutate(self, info, **kwargs):
        config = None
        if "config" in kwargs:
            config = kwargs["config"]
        return model.start_pipeline_execution(info, kwargs["pipeline"].to_selector(), config)


class DauphinMutation(dauphin.ObjectType):
    class Meta:
        name = "Mutation"

    start_pipeline_execution = StartPipelineExecutionMutation.Field()


class DauphinSubscription(dauphin.ObjectType):
    class Meta:
        name = "Subscription"

    pipelineRunLogs = dauphin.Field(
        dauphin.NonNull("PipelineRunLogsSubscriptionPayload"),
        runId=dauphin.Argument(dauphin.NonNull(dauphin.ID)),
        after=dauphin.Argument("Cursor"),
    )

    def resolve_pipelineRunLogs(self, info, runId, after=None):
        return model.get_pipeline_run_observable(info, runId, after)


class DauphinPipelineConfig(dauphin.GenericScalar, dauphin.Scalar):
    class Meta:
        name = "PipelineConfig"
        description = """This type is used when passing in a configuration object
        for pipeline configuration. This is any-typed in the GraphQL type system,
        but must conform to the constraints of the dagster config type system"""


class DauphinExecutionSelector(dauphin.InputObjectType):
    class Meta:
        name = "ExecutionSelector"
        description = """This type represents the fields necessary to identify a
        pipeline or pipeline subset."""

    name = dauphin.NonNull(dauphin.String)
    solidSubset = dauphin.List(dauphin.NonNull(dauphin.String))

    def to_selector(self):
        return ExecutionSelector(self.name, self.solidSubset)
