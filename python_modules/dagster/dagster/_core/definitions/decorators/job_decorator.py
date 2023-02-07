from functools import update_wrapper
from typing import TYPE_CHECKING, AbstractSet, Any, Callable, Mapping, Optional, Union, overload

import dagster._check as check
from dagster._core.decorator_utils import format_docstring_for_description

from ..config import ConfigMapping
from ..graph_definition import GraphDefinition
from ..hook_definition import HookDefinition
from ..job_definition import JobDefinition
from ..logger_definition import LoggerDefinition
from ..metadata import RawMetadataValue
from ..policy import RetryPolicy
from ..resource_definition import ResourceDefinition
from ..version_strategy import VersionStrategy

if TYPE_CHECKING:
    from ..executor_definition import ExecutorDefinition
    from ..partition import PartitionedConfig, PartitionsDefinition


class _Job:
    def __init__(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[Mapping[str, Any]] = None,
        metadata: Optional[Mapping[str, RawMetadataValue]] = None,
        resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
        config: Optional[
            Union[ConfigMapping, Mapping[str, Any], "PartitionedConfig[object]"]
        ] = None,
        logger_defs: Optional[Mapping[str, LoggerDefinition]] = None,
        executor_def: Optional["ExecutorDefinition"] = None,
        hooks: Optional[AbstractSet[HookDefinition]] = None,
        op_retry_policy: Optional[RetryPolicy] = None,
        version_strategy: Optional[VersionStrategy] = None,
        partitions_def: Optional["PartitionsDefinition[object]"] = None,
        input_values: Optional[Mapping[str, object]] = None,
    ):
        self.name = name
        self.description = description
        self.tags = tags
        self.metadata = metadata
        self.resource_defs = resource_defs
        self.config = config
        self.logger_defs = logger_defs
        self.executor_def = executor_def
        self.hooks = hooks
        self.op_retry_policy = op_retry_policy
        self.version_strategy = version_strategy
        self.partitions_def = partitions_def
        self.input_values = input_values

    def __call__(self, fn: Callable[..., Any]) -> JobDefinition:
        check.callable_param(fn, "fn")

        if not self.name:
            self.name = fn.__name__

        from dagster._core.definitions.composition import do_composition

        (
            input_mappings,
            output_mappings,
            dependencies,
            solid_defs,
            config_mapping,
            positional_inputs,
        ) = do_composition(
            decorator_name="@job",
            graph_name=self.name,
            fn=fn,
            provided_input_defs=[],
            provided_output_defs=[],
            ignore_output_from_composition_fn=False,
            config_mapping=None,
        )

        graph_def = GraphDefinition(
            name=self.name,
            dependencies=dependencies,
            node_defs=solid_defs,
            description=self.description or format_docstring_for_description(fn),
            input_mappings=input_mappings,
            output_mappings=output_mappings,
            config=config_mapping,
            positional_inputs=positional_inputs,
            tags=self.tags,
        )

        job_def = graph_def.to_job(
            description=self.description or format_docstring_for_description(fn),
            resource_defs=self.resource_defs,
            config=self.config,
            tags=self.tags,
            metadata=self.metadata,
            logger_defs=self.logger_defs,
            executor_def=self.executor_def,
            hooks=self.hooks,
            op_retry_policy=self.op_retry_policy,
            version_strategy=self.version_strategy,
            partitions_def=self.partitions_def,
            input_values=self.input_values,
        )
        update_wrapper(job_def, fn)
        return job_def


@overload
def job(compose_fn: Callable[..., Any]) -> JobDefinition:
    ...


@overload
def job(
    *,
    name: Optional[str] = ...,
    description: Optional[str] = ...,
    resource_defs: Optional[Mapping[str, ResourceDefinition]] = ...,
    config: Union[ConfigMapping, Mapping[str, Any], "PartitionedConfig[object]"] = ...,
    tags: Optional[Mapping[str, Any]] = ...,
    metadata: Optional[Mapping[str, RawMetadataValue]] = ...,
    logger_defs: Optional[Mapping[str, LoggerDefinition]] = ...,
    executor_def: Optional["ExecutorDefinition"] = ...,
    hooks: Optional[AbstractSet[HookDefinition]] = ...,
    op_retry_policy: Optional[RetryPolicy] = ...,
    version_strategy: Optional[VersionStrategy] = ...,
    partitions_def: Optional["PartitionsDefinition[object]"] = ...,
    input_values: Optional[Mapping[str, object]] = ...,
) -> _Job:
    ...


def job(
    compose_fn: Optional[Callable[..., Any]] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
    config: Optional[Union[ConfigMapping, Mapping[str, Any], "PartitionedConfig[object]"]] = None,
    tags: Optional[Mapping[str, Any]] = None,
    metadata: Optional[Mapping[str, RawMetadataValue]] = None,
    logger_defs: Optional[Mapping[str, LoggerDefinition]] = None,
    executor_def: Optional["ExecutorDefinition"] = None,
    hooks: Optional[AbstractSet[HookDefinition]] = None,
    op_retry_policy: Optional[RetryPolicy] = None,
    version_strategy: Optional[VersionStrategy] = None,
    partitions_def: Optional["PartitionsDefinition[object]"] = None,
    input_values: Optional[Mapping[str, object]] = None,
) -> Union[JobDefinition, _Job]:
    """Creates a job with the specified parameters from the decorated graph/op invocation function.

    Using this decorator allows you to build an executable job by writing a function that invokes
    ops (or graphs).

    Args:
        compose_fn (Callable[..., Any]:
            The decorated function. The body should contain op or graph invocations. Unlike op
            functions, does not accept a context argument.
        name (Optional[str]):
            The name for the Job. Defaults to the name of the this graph.
        resource_defs (Optional[Mapping[str, ResourceDefinition]]):
            Resources that are required by this graph for execution.
            If not defined, `io_manager` will default to filesystem.
        config:
            Describes how the job is parameterized at runtime.

            If no value is provided, then the schema for the job's run config is a standard
            format based on its ops and resources.

            If a dictionary is provided, then it must conform to the standard config schema, and
            it will be used as the job's run config for the job whenever the job is executed.
            The values provided will be viewable and editable in the Dagit playground, so be
            careful with secrets.

            If a :py:class:`ConfigMapping` object is provided, then the schema for the job's run config is
            determined by the config mapping, and the ConfigMapping, which should return
            configuration in the standard format to configure the job.

            If a :py:class:`PartitionedConfig` object is provided, then it defines a discrete set of config
            values that can parameterize the pipeline, as well as a function for mapping those
            values to the base config. The values provided will be viewable and editable in the
            Dagit playground, so be careful with secrets.
        tags (Optional[Dict[str, Any]]):
            Arbitrary information that will be attached to the execution of the Job.
            Values that are not strings will be json encoded and must meet the criteria that
            `json.loads(json.dumps(value)) == value`.  These tag values may be overwritten by tag
            values provided at invocation time.
        metadata (Optional[Dict[str, RawMetadataValue]]):
            Arbitrary information that will be attached to the JobDefinition and be viewable in Dagit.
            Keys must be strings, and values must be python primitive types or one of the provided
            MetadataValue types
        logger_defs (Optional[Dict[str, LoggerDefinition]]):
            A dictionary of string logger identifiers to their implementations.
        executor_def (Optional[ExecutorDefinition]):
            How this Job will be executed. Defaults to :py:class:`multiprocess_executor` .
        op_retry_policy (Optional[RetryPolicy]): The default retry policy for all ops in this job.
            Only used if retry policy is not defined on the op definition or op invocation.
        version_strategy (Optional[VersionStrategy]): (Deprecated)
            Defines how each op (and optionally, resource) in the job can be versioned. If
            provided, memoization will be enabled for this job. This is deprecated in favor of asset
            versioning.
        partitions_def (Optional[PartitionsDefinition]): Defines a discrete set of partition keys
            that can parameterize the job. If this argument is supplied, the config argument
            can't also be supplied.
        input_values (Optional[Mapping[str, Any]]):
            A dictionary that maps python objects to the top-level inputs of a job.

    Examples:
        .. code-block:: python

            @op
            def return_one():
                return 1

            @op
            def add_one(in1):
                return in1 + 1

            @job
            def job1():
                add_one(return_one())
    """
    if compose_fn is not None:
        check.invariant(description is None)
        return _Job()(compose_fn)

    return _Job(
        name=name,
        description=description,
        resource_defs=resource_defs,
        config=config,
        tags=tags,
        metadata=metadata,
        logger_defs=logger_defs,
        executor_def=executor_def,
        hooks=hooks,
        op_retry_policy=op_retry_policy,
        version_strategy=version_strategy,
        partitions_def=partitions_def,
        input_values=input_values,
    )
