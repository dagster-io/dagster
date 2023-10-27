import os
import shutil
import tempfile
from collections import defaultdict
from contextlib import contextmanager
from typing import Any, Dict, List, Mapping, Optional, Type, cast

# top-level include is dangerous in terms of incurring circular deps
from dagster import (
    DagsterInvariantViolationError,
    DependencyDefinition,
    NodeInvocation,
    _check as check,
)
from dagster._config import Field, StringSource
from dagster._config.config_schema import UserConfigSchema
from dagster._core.definitions import (
    GraphDefinition,
    InputMapping,
    JobDefinition,
    OpDefinition,
    OutputMapping,
)
from dagster._core.definitions.dependency import Node
from dagster._core.definitions.executor_definition import in_process_executor
from dagster._core.definitions.job_base import InMemoryJob
from dagster._core.definitions.logger_definition import LoggerDefinition
from dagster._core.definitions.resource_definition import ScopedResourcesBuilder
from dagster._core.execution.api import create_execution_plan
from dagster._core.execution.context.system import PlanExecutionContext
from dagster._core.execution.context_creation_job import (
    create_context_creation_data,
    create_execution_data,
    create_executor,
    create_log_manager,
    create_plan_data,
)
from dagster._core.execution.execute_in_process_result import ExecuteInProcessResult
from dagster._core.instance import DagsterInstance
from dagster._core.scheduler import Scheduler
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.storage.event_log.sqlite.sqlite_event_log import SqliteEventLogStorage
from dagster._core.storage.sqlite_storage import SqliteStorageConfig
from dagster._core.utility_ops import create_stub_op
from dagster._serdes import ConfigurableClass
from dagster._serdes.config_class import ConfigurableClassData
from dagster._utils.concurrency import ConcurrencyClaimStatus

# re-export
from ..temp_file import (
    get_temp_dir as get_temp_dir,
    get_temp_file_handle as get_temp_file_handle,
    get_temp_file_handle_with_data as get_temp_file_handle_with_data,
    get_temp_file_name as get_temp_file_name,
    get_temp_file_name_with_data as get_temp_file_name_with_data,
    get_temp_file_names as get_temp_file_names,
)


def create_test_pipeline_execution_context(
    logger_defs: Optional[Mapping[str, LoggerDefinition]] = None
) -> PlanExecutionContext:
    loggers = check.opt_mapping_param(
        logger_defs, "logger_defs", key_type=str, value_type=LoggerDefinition
    )
    job_def = GraphDefinition(
        name="test_legacy_context",
        node_defs=[],
    ).to_job(executor_def=in_process_executor, logger_defs=logger_defs)
    run_config: Dict[str, Dict[str, Dict]] = {"loggers": {key: {} for key in loggers}}
    dagster_run = DagsterRun(job_name="test_legacy_context", run_config=run_config)
    instance = DagsterInstance.ephemeral()
    execution_plan = create_execution_plan(job=job_def, run_config=run_config)
    creation_data = create_context_creation_data(
        InMemoryJob(job_def),
        execution_plan,
        run_config,
        dagster_run,
        instance,
    )
    log_manager = create_log_manager(creation_data)
    scoped_resources_builder = ScopedResourcesBuilder()
    executor = create_executor(creation_data)

    return PlanExecutionContext(
        plan_data=create_plan_data(creation_data, True, executor.retries),
        execution_data=create_execution_data(
            context_creation_data=creation_data,
            scoped_resources_builder=scoped_resources_builder,
        ),
        log_manager=log_manager,
        output_capture=None,
    )


def _dep_key_of(node: Node) -> NodeInvocation:
    return NodeInvocation(node.definition.name, node.name)


def build_job_with_input_stubs(
    job_def: JobDefinition, inputs: Mapping[str, Mapping[str, object]]
) -> JobDefinition:
    check.inst_param(job_def, "pipeline_def", JobDefinition)
    check.mapping_param(inputs, "inputs", key_type=str, value_type=dict)

    deps: Dict[NodeInvocation, Dict[str, object]] = defaultdict(dict)
    for node_name, dep_dict in job_def.dependencies.items():
        for input_name, dep in dep_dict.items():
            deps[node_name][input_name] = dep

    stub_node_defs = []

    for node_name, input_dict in inputs.items():
        if not job_def.has_node_named(node_name):
            raise DagsterInvariantViolationError(
                f"You are injecting an input value for node {node_name} "
                f"into pipeline {job_def.name} but that node was not found"
            )

        node = job_def.get_node_named(node_name)
        for input_name, input_value in input_dict.items():
            stub_node_def = create_stub_op(
                f"__stub_{node_name}_{input_name}",
                input_value,
            )
            stub_node_defs.append(stub_node_def)
            deps[_dep_key_of(node)][input_name] = DependencyDefinition(stub_node_def.name)

    return JobDefinition(
        name=job_def.name + "_stubbed",
        graph_def=GraphDefinition(
            node_defs=[*job_def.top_level_node_defs, *stub_node_defs],
            dependencies=deps,  # type: ignore
        ),
        resource_defs=job_def.resource_defs,
    )


def wrap_op_in_graph(
    op_def: OpDefinition,
    tags: Optional[Mapping[str, Any]] = None,
    do_input_mapping: bool = True,
    do_output_mapping: bool = True,
) -> GraphDefinition:
    """Wraps op in a graph with the same inputs/outputs as the original op."""
    check.opt_mapping_param(tags, "tags", key_type=str)

    if do_input_mapping:
        input_mappings = []
        for input_name in op_def.ins.keys():
            # create an input mapping to the inner node with the same name.
            input_mappings.append(
                InputMapping(
                    graph_input_name=input_name,
                    mapped_node_name=op_def.name,
                    mapped_node_input_name=input_name,
                )
            )
    else:
        input_mappings = None

    if do_output_mapping:
        output_mappings = []
        for output_name in op_def.outs.keys():
            out = op_def.outs[output_name]
            output_mappings.append(
                OutputMapping(
                    graph_output_name=output_name,
                    mapped_node_name=op_def.name,
                    mapped_node_output_name=output_name,
                    from_dynamic_mapping=out.is_dynamic,
                )
            )
    else:
        output_mappings = None

    return GraphDefinition(
        name=f"wraps_{op_def.name}",
        node_defs=[op_def],
        input_mappings=input_mappings,
        output_mappings=output_mappings,
        tags=tags,
    )


def wrap_op_in_graph_and_execute(
    op_def: OpDefinition,
    resources: Optional[Mapping[str, Any]] = None,
    input_values: Optional[Mapping[str, Any]] = None,
    tags: Optional[Mapping[str, Any]] = None,
    run_config: Optional[Mapping[str, object]] = None,
    raise_on_error: bool = True,
    do_input_mapping: bool = True,
    do_output_mapping: bool = True,
    logger_defs: Optional[Mapping[str, LoggerDefinition]] = None,
) -> ExecuteInProcessResult:
    """Execute a single op in an ephemeral, in-process job.

    Intended to support unit tests. Input values may be passed directly, and no job need be
    specified -- an ephemeral one will be constructed.

    Args:
        op_def (OpDefinition): The op to execute.
        resources (Mapping[str, Any]): Resources that will be passed to `execute_in_process`.
        input_values (Optional[Dict[str, Any]]): A dict of input names to input values, used to
            pass inputs to the solid directly. You may also use the ``run_config`` to
            configure any inputs that are configurable.
        tags (Optional[Dict[str, Any]]): Arbitrary key-value pairs that will be added to pipeline
            logs.
        run_config (Optional[dict]): The configuration that parameterized this
            execution, as a dict.
        raise_on_error (Optional[bool]): Whether or not to raise exceptions when they occur.
            Defaults to ``True``, since this is the most useful behavior in test.
        do_input_mapping (bool): Whether to map the op inputs to the outputs of the graph
            constructed around it.
        do_output_mapping (bool): Whether to map the op outputs to the outputs of the graph
            constructed around it.

    Returns:
        Union[CompositeSolidExecutionResult, SolidExecutionResult]: The result of executing the
        solid.
    """
    return (
        wrap_op_in_graph(
            op_def, tags, do_input_mapping=do_input_mapping, do_output_mapping=do_output_mapping
        )
        .to_job(logger_defs=logger_defs)
        .execute_in_process(
            resources=resources,
            input_values=input_values,
            raise_on_error=raise_on_error,
            run_config=run_config,
        )
    )


@contextmanager
def copy_directory(src):
    with tempfile.TemporaryDirectory() as temp_dir:
        dst = os.path.join(temp_dir, os.path.basename(src))
        shutil.copytree(src, dst)
        yield dst


class FilesystemTestScheduler(Scheduler, ConfigurableClass):
    """This class is used in dagster core and dagster_graphql to test the scheduler's interactions
    with schedule storage, which are implemented in the methods defined on the base Scheduler class.
    Therefore, the following methods used to actually schedule jobs (e.g. create and remove cron jobs
    on a cron tab) are left unimplemented.
    """

    def __init__(self, artifacts_dir: str, inst_data: object = None):
        check.str_param(artifacts_dir, "artifacts_dir")
        self._artifacts_dir = artifacts_dir
        self._inst_data = inst_data

    @property
    def inst_data(self) -> object:
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {"base_dir": str}

    @classmethod
    def from_config_value(
        cls, inst_data: object, config_value: Mapping[str, object]
    ) -> "FilesystemTestScheduler":
        artifacts_dir = cast(str, config_value["base_dir"])
        return FilesystemTestScheduler(artifacts_dir=artifacts_dir, inst_data=inst_data)

    def debug_info(self) -> str:
        return ""

    def get_logs_path(self, _instance: DagsterInstance, schedule_origin_id: str) -> str:
        check.str_param(schedule_origin_id, "schedule_origin_id")
        return os.path.join(self._artifacts_dir, "logs", schedule_origin_id, "scheduler.log")

    def wipe(self, instance: DagsterInstance) -> None:
        pass


class TestStorageConfig(SqliteStorageConfig):
    # interval to sleep between claim checks
    sleep_interval: int


class ConcurrencyEnabledSqliteTestEventLogStorage(SqliteEventLogStorage, ConfigurableClass):
    """Sqlite is sorta supported for concurrency, as long as the rate of concurrent writes is tolerably
    low.  Officially, we should not support, but in the spirit of getting code coverage in the core
    dagster package, let's mark it as that.
    """

    __test__ = False

    def __init__(
        self,
        base_dir: str,
        sleep_interval: Optional[float] = None,
        inst_data: Optional[ConfigurableClassData] = None,
    ):
        self._sleep_interval = sleep_interval
        self._check_calls = defaultdict(int)
        super().__init__(base_dir, inst_data)

    @classmethod
    def config_type(cls) -> UserConfigSchema:
        return {"base_dir": StringSource, "sleep_interval": Field(float, is_required=False)}

    @classmethod
    def from_config_value(
        cls, inst_data: Optional[ConfigurableClassData], config_value: TestStorageConfig
    ) -> "ConcurrencyEnabledSqliteTestEventLogStorage":
        return ConcurrencyEnabledSqliteTestEventLogStorage(inst_data=inst_data, **config_value)

    @property
    def supports_global_concurrency_limits(self) -> bool:
        return True

    def get_check_calls(self, step_key: str) -> int:
        return self._check_calls[step_key]

    def check_concurrency_claim(
        self, concurrency_key: str, run_id: str, step_key: str
    ) -> ConcurrencyClaimStatus:
        self._check_calls[step_key] += 1
        claim_status = super().check_concurrency_claim(concurrency_key, run_id, step_key)
        if not self._sleep_interval:
            return claim_status
        return claim_status.with_sleep_interval(float(self._sleep_interval))


def get_all_direct_subclasses_of_marker(marker_interface_cls: Type) -> List[Type]:
    import dagster as dagster

    return [
        symbol
        for symbol in dagster.__dict__.values()
        if isinstance(symbol, type)
        and issubclass(symbol, marker_interface_cls)
        and marker_interface_cls
        in symbol.__bases__  # ensure that the class is a direct subclass of marker_interface_cls (not a subclass of a subclass)
    ]
