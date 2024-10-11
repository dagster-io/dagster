import csv
import datetime
import gc
import logging
import os
import string
import time
from collections import OrderedDict
from contextlib import contextmanager
from copy import deepcopy
from typing import Iterator, List, Mapping, Optional, Sequence, Tuple, TypeVar, Union

from dagster import (
    Any,
    AssetCheckKey,
    AssetCheckResult,
    AssetCheckSpec,
    AssetExecutionContext,
    AssetIn,
    AssetKey,
    AssetMaterialization,
    AssetObservation,
    AssetOut,
    AssetsDefinition,
    AssetSelection,
    AutoMaterializePolicy,
    BackfillPolicy,
    Bool,
    DagsterInstance,
    DailyPartitionsDefinition,
    DefaultScheduleStatus,
    DefaultSensorStatus,
    DynamicOut,
    DynamicOutput,
    DynamicPartitionsDefinition,
    Enum,
    EnumValue,
    ExpectationResult,
    Field,
    HourlyPartitionsDefinition,
    In,
    Int,
    IOManager,
    IOManagerDefinition,
    Map,
    Noneable,
    Nothing,
    OpExecutionContext,
    Out,
    Output,
    PythonObjectDagsterType,
    ScheduleDefinition,
    SensorResult,
    SourceAsset,
    StaticPartitionsDefinition,
    String,
    TableColumn,
    TableColumnConstraints,
    TableConstraints,
    TableRecord,
    TableSchema,
    TimeWindowPartitionMapping,
    WeeklyPartitionsDefinition,
    _check as check,
    asset,
    asset_check,
    asset_sensor,
    dagster_type_loader,
    daily_partitioned_config,
    define_asset_job,
    freshness_policy_sensor,
    graph,
    job,
    logger,
    multi_asset,
    multi_asset_sensor,
    op,
    repository,
    resource,
    run_failure_sensor,
    run_status_sensor,
    schedule,
    static_partitioned_config,
    usable_as_dagster_type,
)
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.automation_condition_sensor_definition import (
    AutomationConditionSensorDefinition,
)
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._core.definitions.decorators.sensor_decorator import sensor
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import Failure
from dagster._core.definitions.executor_definition import in_process_executor
from dagster._core.definitions.external_asset import external_asset_from_spec
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.definitions.multi_dimensional_partitions import MultiPartitionsDefinition
from dagster._core.definitions.partition import PartitionedConfig
from dagster._core.definitions.reconstruct import ReconstructableRepository
from dagster._core.definitions.sensor_definition import RunRequest, SensorDefinition, SkipReason
from dagster._core.definitions.unresolved_asset_job_definition import UnresolvedAssetJobDefinition
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.log_manager import coerce_valid_log_level
from dagster._core.remote_representation.external import RemoteRepository
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.storage.tags import RESUME_RETRY_TAG
from dagster._core.workspace.context import WorkspaceProcessContext, WorkspaceRequestContext
from dagster._core.workspace.load_target import PythonFileTarget
from dagster._seven import get_system_temp_directory
from dagster._utils import file_relative_path, segfault
from dagster_graphql.test.utils import (
    define_out_of_process_context,
    infer_job_selector,
    main_repo_location_name,
    main_repo_name,
)
from typing_extensions import Literal, Never

T = TypeVar("T")

LONG_INT = 2875972244  # 32b unsigned, > 32b signed


@dagster_type_loader(String)
def df_input_schema(_context, path: str) -> Sequence[OrderedDict]:
    with open(path, "r", encoding="utf8") as fd:
        return [OrderedDict(sorted(x.items(), key=lambda x: x[0])) for x in csv.DictReader(fd)]


PoorMansDataFrame = PythonObjectDagsterType(
    python_type=list,
    name="PoorMansDataFrame",
    loader=df_input_schema,
)


@contextmanager
def define_test_out_of_process_context(
    instance: DagsterInstance,
) -> Iterator[WorkspaceRequestContext]:
    check.inst_param(instance, "instance", DagsterInstance)
    with define_out_of_process_context(__file__, main_repo_name(), instance) as context:
        yield context


def create_main_recon_repo():
    return ReconstructableRepository.for_file(__file__, main_repo_name())


@contextmanager
def get_workspace_process_context(instance: DagsterInstance) -> Iterator[WorkspaceProcessContext]:
    with WorkspaceProcessContext(
        instance,
        PythonFileTarget(
            python_file=file_relative_path(__file__, "repo.py"),
            attribute=main_repo_name(),
            working_directory=None,
            location_name=main_repo_location_name(),
        ),
    ) as workspace_process_context:
        yield workspace_process_context


@contextmanager
def get_main_workspace(instance: DagsterInstance) -> Iterator[WorkspaceRequestContext]:
    with WorkspaceProcessContext(
        instance,
        PythonFileTarget(
            python_file=file_relative_path(__file__, "repo.py"),
            attribute=main_repo_name(),
            working_directory=None,
            location_name=main_repo_location_name(),
        ),
    ) as workspace_process_context:
        yield workspace_process_context.create_request_context()


@contextmanager
def get_main_remote_repo(instance: DagsterInstance) -> Iterator[RemoteRepository]:
    with get_main_workspace(instance) as workspace:
        location = workspace.get_code_location(main_repo_location_name())
        yield location.get_repository(main_repo_name())


@op(
    ins={"num": In(PoorMansDataFrame)},
    out=Out(PoorMansDataFrame),
)
def sum_op(num):
    sum_df = deepcopy(num)
    for x in sum_df:
        x["sum"] = int(x["num1"]) + int(x["num2"])
    return sum_df


@op(
    ins={"sum_df": In(PoorMansDataFrame)},
    out=Out(PoorMansDataFrame),
)
def sum_sq_op(sum_df):
    sum_sq_df = deepcopy(sum_df)
    for x in sum_sq_df:
        x["sum_sq"] = int(x["sum"]) ** 2
    return sum_sq_df


@op(
    ins={"sum_df": In(PoorMansDataFrame)},
    out=Out(PoorMansDataFrame),
)
def df_expectations_op(_context, sum_df):
    yield ExpectationResult(label="some_expectation", success=True)
    yield ExpectationResult(label="other_expectation", success=True)
    yield Output(sum_df)


def csv_hello_world_ops_config():
    return {"ops": {"sum_op": {"inputs": {"num": file_relative_path(__file__, "../data/num.csv")}}}}


@op(config_schema={"file": Field(String)})
def loop(context):
    with open(context.op_config["file"], "w", encoding="utf8") as ff:
        ff.write("yup")

    while True:
        time.sleep(0.1)


@job
def infinite_loop_job():
    loop()


@op
def noop_op(_):
    pass


@job
def noop_job():
    noop_op()


@op
def op_asset_a(_):
    yield AssetMaterialization(asset_key="a")
    yield Output(1)


@op
def op_asset_b(_, num):
    yield AssetMaterialization(asset_key="b")
    time.sleep(0.1)
    yield AssetMaterialization(asset_key="c")
    yield Output(num)


@op
def op_partitioned_asset(_):
    yield AssetMaterialization(asset_key="a", partition="partition_1")
    yield Output(1)


@op
def tag_asset_op(_):
    yield AssetMaterialization(asset_key="a")
    yield Output(1)


@job
def single_asset_job():
    op_asset_a()


@job
def multi_asset_job():
    op_asset_b(op_asset_a())


@job
def partitioned_asset_job():
    op_partitioned_asset()


@job
def asset_tag_job():
    tag_asset_op()


@job
def job_with_expectations():
    @op(out={})
    def emit_successful_expectation(_context):
        yield ExpectationResult(
            success=True,
            label="always_true",
            description="Successful",
            metadata={"data": {"reason": "Just because."}},
        )

    @op(out={})
    def emit_failed_expectation(_context):
        yield ExpectationResult(
            success=False,
            label="always_false",
            description="Failure",
            metadata={"data": {"reason": "Relentless pessimism."}},
        )

    @op(out={})
    def emit_successful_expectation_no_metadata(_context):
        yield ExpectationResult(success=True, label="no_metadata", description="Successful")

    emit_successful_expectation()
    emit_failed_expectation()
    emit_successful_expectation_no_metadata()


@job
def more_complicated_config():
    @op(
        config_schema={
            "field_one": Field(String),
            "field_two": Field(String, is_required=False),
            "field_three": Field(String, is_required=False, default_value="some_value"),
        }
    )
    def op_with_three_field_config(_context):
        return None

    noop_op()
    op_with_three_field_config()


@job
def config_with_map():
    @op(
        config_schema={
            "field_one": Field(Map(str, int, key_label_name="username")),
            "field_two": Field({bool: int}, is_required=False),
            "field_three": Field(
                {str: {"nested": [Noneable(int)]}},
                is_required=False,
                default_value={"test": {"nested": [None, 1, 2]}},
            ),
        }
    )
    def op_with_map_config(_context):
        return None

    noop_op()
    op_with_map_config()


@job
def more_complicated_nested_config():
    @op(
        name="op_with_multilayered_config",
        config_schema={
            "field_any": Any,
            "field_one": String,
            "field_two": Field(String, is_required=False),
            "field_three": Field(String, is_required=False, default_value="some_value"),
            "nested_field": {
                "field_four_str": String,
                "field_five_int": Int,
                "field_six_nullable_int_list": Field([Noneable(int)], is_required=False),
            },
        },
        out={},
    )
    def op_with_multilayered_config(_):
        return None

    op_with_multilayered_config()


@job
def csv_hello_world():
    sum_sq_op(sum_df=sum_op())


@job
def csv_hello_world_with_expectations():
    ss = sum_op()
    sum_sq_op(sum_df=ss)
    df_expectations_op(sum_df=ss)


@job
def csv_hello_world_two():
    sum_op()


@op
def op_that_gets_tags(context):
    return context.run.tags


@job(tags={"tag_key": "tag_value"})
def hello_world_with_tags():
    op_that_gets_tags()


@op(name="op_with_list", ins={}, out={}, config_schema=[int])
def op_def(_):
    return None


@job
def job_with_input_output_metadata():
    @op(
        ins={"foo": In(Int, metadata={"a": "b"})},
        out={"bar": Out(Int, metadata={"c": "d"})},
    )
    def op_with_input_output_metadata(foo):
        return foo + 1

    op_with_input_output_metadata()


@job
def job_with_list():
    op_def()


@job
def csv_hello_world_df_input():
    sum_sq_op(sum_op())


integers_partitions = StaticPartitionsDefinition([str(i) for i in range(10)])

integers_config = PartitionedConfig(
    partitions_def=integers_partitions,
    run_config_for_partition_fn=lambda partition: {},
    tags_for_partition_fn=lambda partition: {"foo": partition.name},
)


@job(partitions_def=integers_partitions, config=integers_config)
def integers():
    @op
    def return_integer():
        return 1

    return_integer()


@asset(partitions_def=integers_partitions, backfill_policy=BackfillPolicy.single_run())
def integers_asset(context: AssetExecutionContext):
    return {k: 1 for k in context.partition_keys}


integers_asset_job = define_asset_job("integers_asset_job", selection=[integers_asset])

alpha_partitions = StaticPartitionsDefinition(list(string.ascii_lowercase))


@job(partitions_def=alpha_partitions)
def no_config_job():
    @op
    def return_hello():
        return "Hello"

    return_hello()


@job
def no_config_chain_job():
    @op
    def return_foo():
        return "foo"

    @op
    def return_hello_world(_foo):
        return "Hello World"

    return_hello_world(return_foo())


@job
def scalar_output_job():
    @op(out=Out(String))
    def return_str():
        return "foo"

    @op(out=Out(Int))
    def return_int():
        return 34234

    @op(out=Out(Bool))
    def return_bool():
        return True

    @op(out=Out(Any))
    def return_any():
        return "dkjfkdjfe"

    return_str()
    return_int()
    return_bool()
    return_any()


@job
def job_with_enum_config():
    @op(
        config_schema=Enum(
            "TestEnum",
            [
                EnumValue(config_value="ENUM_VALUE_ONE", description="An enum value."),
                EnumValue(config_value="ENUM_VALUE_TWO", description="An enum value."),
                EnumValue(config_value="ENUM_VALUE_THREE", description="An enum value."),
            ],
        )
    )
    def takes_an_enum(_context):
        pass

    takes_an_enum()


@job
def naughty_programmer_job():
    @op
    def throw_a_thing():
        try:
            try:
                try:
                    raise Exception("The inner sanctum")
                except:
                    raise Exception("bad programmer, bad")
            except Exception as e:
                raise Exception("Outer exception") from e
        except Exception as e:
            # throw a Failure here so we can test metadata
            raise Failure("Even more outer exception", metadata={"top_level": True}) from e

    throw_a_thing()


@job
def job_with_invalid_definition_error():
    @usable_as_dagster_type(name="InputTypeWithoutHydration")
    class InputTypeWithoutHydration(int):
        pass

    @op(out=Out(InputTypeWithoutHydration))
    def one(_):
        return 1

    @op(
        ins={"some_input": In(InputTypeWithoutHydration)},
        out=Out(int),
    )
    def fail_subset(_, some_input):
        return some_input

    fail_subset(one())


@resource(config_schema=Field(Int))
def adder_resource(init_context):
    return lambda x: x + init_context.resource_config


@resource(config_schema=Field(Int))
def multer_resource(init_context):
    return lambda x: x * init_context.resource_config


@resource(config_schema={"num_one": Field(Int), "num_two": Field(Int)})
def double_adder_resource(init_context):
    return (
        lambda x: x
        + init_context.resource_config["num_one"]
        + init_context.resource_config["num_two"]
    )


@resource(config_schema=Field(Int, is_required=False))
def req_resource(_):
    return 1


@op(required_resource_keys={"R1"})
def op_with_required_resource(_):
    return 1


@job(resource_defs={"R1": req_resource})
def required_resource_job():
    op_with_required_resource()


@resource(config_schema=Field(Int))
def req_resource_config(_):
    return 1


@job(resource_defs={"R1": req_resource_config})
def required_resource_config_job():
    op_with_required_resource()


@logger(config_schema=Field(str))
def foo_logger(init_context):
    logger_ = logging.Logger("foo")
    logger_.setLevel(coerce_valid_log_level(init_context.logger_config))
    return logger_


@logger({"log_level": Field(str), "prefix": Field(str)})
def bar_logger(init_context):
    class BarLogger(logging.Logger):
        def __init__(self, name, prefix, *args, **kwargs):
            self.prefix = prefix
            super(BarLogger, self).__init__(name, *args, **kwargs)

        def log(self, lvl, msg, *args, **kwargs):
            msg = self.prefix + msg
            super(BarLogger, self).log(lvl, msg, *args, **kwargs)

    logger_ = BarLogger("bar", init_context.logger_config["prefix"])
    logger_.setLevel(coerce_valid_log_level(init_context.logger_config["log_level"]))


@job(
    logger_defs={"foo": foo_logger, "bar": bar_logger},
)
def loggers_job():
    @op
    def return_six(context):
        context.log.critical("OMG!")
        return 6

    return_six()


@job
def composites_job():
    @op(ins={"num": In(Int)}, out=Out(Int))
    def add_one(num):
        return num + 1

    @op(ins={"num": In()})
    def div_two(num):
        return num / 2

    @graph
    def add_two(num: int) -> int:
        return add_one.alias("adder_2")(add_one.alias("adder_1")(num))

    @graph
    def add_four(num: int) -> int:
        return add_two.alias("adder_2")(add_two.alias("adder_1")(num))

    @graph
    def div_four(num):
        return div_two.alias("div_2")(div_two.alias("div_1")(num))

    div_four(add_four())


@job
def materialization_job():
    @op
    def materialize(_):
        yield AssetMaterialization(
            asset_key="all_types",
            description="a materialization with all metadata types",
            metadata={
                "text": "text is cool",
                "url": MetadataValue.url("https://bigty.pe/neato"),
                "path": MetadataValue.path("/tmp/awesome"),
                "json": {"is_dope": True},
                "python class": MetadataValue.python_artifact(AssetMaterialization),
                "python_function": MetadataValue.python_artifact(file_relative_path),
                "float": 1.2,
                "int": 1,
                "float NaN": float("nan"),
                "long int": LONG_INT,
                "pipeline run": MetadataValue.dagster_run("fake_run_id"),
                "my asset": AssetKey("my_asset"),
                "table": MetadataValue.table(
                    records=[
                        TableRecord(dict(foo=1, bar=2)),
                        TableRecord(dict(foo=3, bar=4)),
                    ],
                ),
                "table_schema": TableSchema(
                    columns=[
                        TableColumn(
                            name="foo",
                            type="integer",
                            constraints=TableColumnConstraints(unique=True),
                            tags={"foo": "bar"},
                        ),
                        TableColumn(name="bar", type="string"),
                    ],
                    constraints=TableConstraints(
                        other=["some constraint"],
                    ),
                ),
                "my job": MetadataValue.job("materialization_job", location_name="test_location"),
            },
        )
        yield Output(None)

    materialize()


@job
def spew_job():
    @op
    def spew(_):
        print("HELLO WORLD")  # noqa: T201

    spew()


def retry_config(count):
    return {
        "resources": {"retry_count": {"config": {"count": count}}},
    }


@resource(config_schema={"count": Field(Int, is_required=False, default_value=0)})
def retry_config_resource(context):
    return context.resource_config["count"]


@job(
    resource_defs={
        "retry_count": retry_config_resource,
    }
)
def eventually_successful():
    @op
    def spawn() -> int:
        return 0

    @op(
        required_resource_keys={"retry_count"},
    )
    def fail(context: OpExecutionContext, depth: int) -> int:
        if context.resources.retry_count <= depth:
            raise Exception("fail")

        return depth + 1

    @op
    def reset(depth: int) -> int:
        return depth

    @op
    def collect(fan_in: List[int]):
        if fan_in != [1, 2, 3]:
            raise Exception(f"Fan in failed, expected [1, 2, 3] got {fan_in}")

    s = spawn()
    f1 = fail(s)
    f2 = fail(f1)
    f3 = fail(f2)
    reset(f3)
    collect([f1, f2, f3])


# The tests that use this rely on it using in-process execution.
@job
def hard_failer():
    @op(
        config_schema={"fail": Field(Bool, is_required=False, default_value=False)},
    )
    def hard_fail_or_0(context) -> int:
        if context.op_config["fail"]:
            segfault()
        return 0

    @op
    def increment(_, n: int) -> int:
        return n + 1

    increment(hard_fail_or_0())


@resource
def resource_a(_):
    return "A"


@resource
def resource_b(_):
    return "B"


@op(required_resource_keys={"a"})
def start(context):
    assert context.resources.a == "A"
    return 1


@op(required_resource_keys={"b"})
def will_fail(context, num):
    assert context.resources.b == "B"
    raise Exception("fail")


@job(
    resource_defs={
        "a": resource_a,
        "b": resource_b,
    }
)
def retry_resource_job():
    will_fail(start())


@op(
    config_schema={"fail": bool},
    ins={"inp": In(str)},
    out={
        "start_fail": Out(str, is_required=False),
        "start_skip": Out(str, is_required=False),
    },
)
def can_fail(context, inp):
    if context.op_config["fail"]:
        raise Exception("blah")

    yield Output("okay perfect", "start_fail")


@op(
    out={
        "success": Out(str, is_required=False),
        "skip": Out(str, is_required=False),
    },
)
def multi(_):
    yield Output("okay perfect", "success")


@op
def passthrough(_, value):
    return value


@op(ins={"start": In(Nothing)}, out={})
def no_output(_):
    yield ExpectationResult(True)


@job
def retry_multi_output_job():
    multi_success, multi_skip = multi()
    fail, skip = can_fail(multi_success)
    no_output.alias("child_multi_skip")(multi_skip)
    no_output.alias("child_skip")(skip)
    no_output.alias("grandchild_fail")(passthrough.alias("child_fail")(fail))


@job(tags={"foo": "bar"}, run_tags={"baz": "quux"})
def tagged_job():
    @op
    def simple_op():
        return "Hello"

    simple_op()


@resource
def disable_gc(_context):
    # Workaround for termination signals being raised during GC and getting swallowed during
    # tests
    try:
        print("Disabling GC")  # noqa: T201
        gc.disable()
        yield
    finally:
        print("Re-enabling GC")  # noqa: T201
        gc.enable()


@job(
    resource_defs={"disable_gc": disable_gc},
)
def retry_multi_input_early_terminate_job():
    @op(out=Out(Int))
    def return_one():
        return 1

    @op(
        config_schema={"wait_to_terminate": bool},
        required_resource_keys={"disable_gc"},
    )
    def get_input_one(context, one: int) -> int:
        if context.op_config["wait_to_terminate"]:
            while True:
                time.sleep(0.1)
        return one

    @op(
        config_schema={"wait_to_terminate": bool},
        required_resource_keys={"disable_gc"},
    )
    def get_input_two(context, one: int) -> int:
        if context.op_config["wait_to_terminate"]:
            while True:
                time.sleep(0.1)
        return one

    @op
    def sum_inputs(input_one: int, input_two: int) -> int:
        return input_one + input_two

    step_one = return_one()
    sum_inputs(input_one=get_input_one(step_one), input_two=get_input_two(step_one))


@job
def dynamic_job():
    @op
    def multiply_by_two(context, y):
        context.log.info("multiply_by_two is returning " + str(y * 2))
        return y * 2

    @op
    def multiply_inputs(context, y, ten, should_fail):
        current_run = context.instance.get_run_by_id(context.run_id)
        if should_fail:
            if y == 2 and current_run.parent_run_id is None:
                raise Exception()
        context.log.info("multiply_inputs is returning " + str(y * ten))
        return y * ten

    @op
    def emit_ten(_):
        return 10

    @op(out=DynamicOut())
    def emit(_):
        for i in range(3):
            yield DynamicOutput(value=i, mapping_key=str(i))

    @op
    def sum_numbers(_, nums):
        return sum(nums)

    multiply_by_two.alias("double_total")(
        sum_numbers(
            emit()
            .map(
                lambda n: multiply_by_two(multiply_inputs(n, emit_ten())),
            )
            .collect(),
        )
    )


@job
def basic_job():
    pass


def get_retry_multi_execution_params(
    graphql_context: WorkspaceRequestContext, should_fail: bool, retry_id: Optional[str] = None
) -> Mapping[str, Any]:
    selector = infer_job_selector(graphql_context, "retry_multi_output_job")
    return {
        "mode": "default",
        "selector": selector,
        "runConfigData": {
            "ops": {"can_fail": {"config": {"fail": should_fail}}},
        },
        "executionMetadata": {
            "rootRunId": retry_id,
            "parentRunId": retry_id,
            "tags": [{"key": RESUME_RETRY_TAG, "value": "true"}] if retry_id else [],
        },
    }


def define_schedules():
    no_config_job_hourly_schedule = ScheduleDefinition(
        name="no_config_job_hourly_schedule",
        cron_schedule="0 0 * * *",
        job_name="no_config_job",
    )

    no_config_job_hourly_schedule_with_config_fn = ScheduleDefinition(
        name="no_config_job_hourly_schedule_with_config_fn",
        cron_schedule="0 0 * * *",
        job_name="no_config_job",
    )

    no_config_should_execute = ScheduleDefinition(
        name="no_config_should_execute",
        cron_schedule="0 0 * * *",
        job_name="no_config_job",
        should_execute=lambda _context: False,
    )

    dynamic_config = ScheduleDefinition(
        name="dynamic_config",
        cron_schedule="0 0 * * *",
        job_name="no_config_job",
    )

    def get_cron_schedule(
        delta: datetime.timedelta, schedule_type: Literal["daily", "hourly"] = "daily"
    ) -> str:
        time = (datetime.datetime.now() + delta).time()
        hour = time.hour if schedule_type == "daily" else "*"
        return f"{time.minute} {hour} * * *"

    def throw_error() -> Never:
        raise Exception("This is an error")

    @schedule(
        cron_schedule=get_cron_schedule(datetime.timedelta(hours=2)),
        job_name="no_config_job",
        default_status=DefaultScheduleStatus.RUNNING,
    )
    def running_in_code_schedule(_context):
        return {}

    # Schedules for testing the user error boundary
    @schedule(
        cron_schedule="@daily",
        job_name="no_config_job",
        should_execute=lambda _: throw_error(),
    )
    def should_execute_error_schedule(_context):
        return {}

    @schedule(
        cron_schedule="@daily",
        job_name="no_config_job",
        tags_fn=lambda _: throw_error(),
    )
    def tags_error_schedule(_context):
        return {}

    @schedule(
        cron_schedule="@daily",
        job_name="no_config_job",
    )
    def run_config_error_schedule(_context):
        throw_error()

    @schedule(
        cron_schedule="@daily",
        job_name="no_config_job",
        execution_timezone="US/Central",
        tags={"foo": "bar"},
        metadata={"foo": "bar"},
    )
    def timezone_schedule_with_tags_and_metadata(_context):
        return {}

    tagged_job_schedule = ScheduleDefinition(
        name="tagged_job_schedule",
        cron_schedule="0 0 * * *",
        job_name="tagged_job",
    )

    tagged_job_override_schedule = ScheduleDefinition(
        name="tagged_job_override_schedule",
        cron_schedule="0 0 * * *",
        job_name="tagged_job",
        tags={"foo": "notbar"},
    )

    invalid_config_schedule = ScheduleDefinition(
        name="invalid_config_schedule",
        cron_schedule="0 0 * * *",
        job_name="job_with_enum_config",
        run_config={"ops": {"takes_an_enum": {"config": "invalid"}}},
    )

    @schedule(
        job_name="nested_job",
        cron_schedule=["45 23 * * 6", "30 9 * * 0"],
    )
    def composite_cron_schedule(_context):
        return {}

    @schedule(
        cron_schedule="* * * * *", job=basic_job, default_status=DefaultScheduleStatus.RUNNING
    )
    def past_tick_schedule():
        return {}

    @schedule(cron_schedule="* * * * *", job=req_config_job)
    def provide_config_schedule():
        return {"ops": {"the_op": {"config": {"foo": "bar"}}}}

    @schedule(cron_schedule="* * * * *", job=req_config_job)
    def always_error():
        raise Exception("darnit")

    @schedule(cron_schedule="* * * * *", target=[asset_one])
    def jobless_schedule(_):
        pass

    return [
        asset_job_schedule,
        run_config_error_schedule,
        no_config_job_hourly_schedule,
        no_config_job_hourly_schedule_with_config_fn,
        no_config_should_execute,
        dynamic_config,
        should_execute_error_schedule,
        tagged_job_schedule,
        tagged_job_override_schedule,
        tags_error_schedule,
        timezone_schedule_with_tags_and_metadata,
        invalid_config_schedule,
        running_in_code_schedule,
        composite_cron_schedule,
        past_tick_schedule,
        provide_config_schedule,
        always_error,
        jobless_schedule,
    ]


def define_sensors():
    @sensor(job_name="no_config_job", tags={"foo": "bar"}, metadata={"foo": "bar"})
    def always_no_config_sensor_with_tags_and_metadata(_):
        return RunRequest(
            run_key=None,
            tags={"test": "1234"},
        )

    @sensor(job_name="no_config_job")
    def always_error_sensor(_):
        raise Exception("OOPS")

    @sensor(job_name="no_config_job")
    def update_cursor_sensor(context):
        if not context.cursor:
            cursor = 0
        else:
            cursor = int(context.cursor)
        cursor += 1
        context.update_cursor(str(cursor))

    @sensor(job_name="no_config_job")
    def once_no_config_sensor(_):
        return RunRequest(
            run_key="once",
            tags={"test": "1234"},
        )

    @sensor(job_name="no_config_job")
    def never_no_config_sensor(_):
        return SkipReason("never")

    @sensor(job_name="dynamic_partitioned_assets_job")
    def dynamic_partition_requesting_sensor(_):
        yield SensorResult(
            run_requests=[RunRequest(partition_key="new_key")],
            dynamic_partitions_requests=[
                DynamicPartitionsDefinition(name="foo").build_add_request(
                    ["new_key", "new_key2", "existent_key"]
                ),
                DynamicPartitionsDefinition(name="foo").build_delete_request(
                    ["old_key", "nonexistent_key"]
                ),
            ],
        )

    @sensor(job_name="no_config_job")
    def multi_no_config_sensor(_):
        yield RunRequest(run_key="A")
        yield RunRequest(run_key="B")

    @sensor(job_name="no_config_job", minimum_interval_seconds=60)
    def custom_interval_sensor(_):
        return RunRequest(
            run_key=None,
            tags={"test": "1234"},
        )

    @sensor(job_name="no_config_job", default_status=DefaultSensorStatus.RUNNING)
    def running_in_code_sensor(_):
        return RunRequest(
            run_key=None,
            tags={"test": "1234"},
        )

    @sensor(job_name="no_config_job", default_status=DefaultSensorStatus.STOPPED)
    def stopped_in_code_sensor(_):
        return RunRequest(
            run_key=None,
            tags={"test": "1234"},
        )

    @sensor(job_name="no_config_job")
    def logging_sensor(context):
        context.log.info("hello hello")

        try:
            raise Exception("hi hi")
        except Exception:
            context.log.exception("goodbye goodbye")

        return SkipReason()

    @sensor(asset_selection=AssetSelection.all())
    def every_asset_sensor(_):
        return SkipReason("just kidding")

    @sensor(asset_selection=AssetSelection.keys("does_not_exist"))
    def invalid_asset_selection_error(_):
        return SkipReason("just kidding")

    @run_status_sensor(run_status=DagsterRunStatus.SUCCESS, request_job=no_config_job)
    def run_status(_):
        return SkipReason("always skip")

    @asset_sensor(asset_key=AssetKey("foo"), job=single_asset_job)
    def single_asset_sensor():
        pass

    @multi_asset_sensor(monitored_assets=[], job=single_asset_job)
    def many_asset_sensor(_):
        pass

    @freshness_policy_sensor(asset_selection=AssetSelection.all())
    def fresh_sensor(_):
        pass

    @run_failure_sensor
    def the_failure_sensor():
        pass

    @sensor(target=[asset_one])
    def jobless_sensor(_):
        pass

    auto_materialize_sensor = AutomationConditionSensorDefinition(
        "my_auto_materialize_sensor",
        asset_selection=AssetSelection.assets(
            "fresh_diamond_bottom", "asset_with_automation_condition"
        ),
    )

    return [
        always_no_config_sensor_with_tags_and_metadata,
        always_error_sensor,
        once_no_config_sensor,
        never_no_config_sensor,
        dynamic_partition_requesting_sensor,
        multi_no_config_sensor,
        custom_interval_sensor,
        running_in_code_sensor,
        stopped_in_code_sensor,
        logging_sensor,
        update_cursor_sensor,
        run_status,
        single_asset_sensor,
        many_asset_sensor,
        fresh_sensor,
        the_failure_sensor,
        auto_materialize_sensor,
        every_asset_sensor,
        invalid_asset_selection_error,
        jobless_sensor,
    ]


# The tests that use this rely on it using in-process execution.
@job(partitions_def=integers_partitions)
def chained_failure_job():
    @op
    def always_succeed():
        return "hello"

    @op
    def conditionally_fail(_upstream):
        if os.path.isfile(
            os.path.join(
                get_system_temp_directory(),
                "chained_failure_job_conditionally_fail",
            )
        ):
            raise Exception("blah")

        return "hello"

    @op
    def after_failure(_upstream):
        return "world"

    after_failure(conditionally_fail(always_succeed()))


@graph
def simple_graph():
    noop_op()


@graph
def composed_graph():
    simple_graph()


@job(config={"ops": {"op_with_config": {"config": {"one": "hullo"}}}})
def job_with_default_config():
    @op(config_schema={"one": Field(String)})
    def op_with_config(context):
        return context.op_config["one"]

    op_with_config()


@resource(config_schema={"file": Field(String)})
def hanging_asset_resource(context):
    # Hack to allow asset to get value from run config
    return context.resource_config.get("file")


class DummyIOManager(IOManager):
    def handle_output(self, context, obj):
        pass

    def load_input(self, context):
        pass


dummy_io_manager = IOManagerDefinition.hardcoded_io_manager(DummyIOManager())

dummy_source_asset = SourceAsset(
    key=AssetKey("dummy_source_asset"), io_manager_key="dummy_io_manager"
)


@asset(io_manager_key="dummy_io_manager")
def first_asset(dummy_source_asset):
    return 1


@asset(io_manager_key="dummy_io_manager", required_resource_keys={"hanging_asset_resource"})
def hanging_asset(context, first_asset):
    """Asset that hangs forever, used to test in-progress ops."""
    with open(context.resources.hanging_asset_resource, "w", encoding="utf8") as ff:
        ff.write("yup")  # signals test to terminate run

    while True:
        time.sleep(0.1)


@asset(io_manager_key="dummy_io_manager")
def never_runs_asset(hanging_asset):
    pass


hanging_job = define_asset_job(
    name="hanging_job",
    selection=[first_asset, hanging_asset, never_runs_asset],
)


@asset(io_manager_key="dummy_io_manager", required_resource_keys={"hanging_asset_resource"})
def output_then_hang_asset(context):
    yield Output(5)
    with open(context.resources.hanging_asset_resource, "w", encoding="utf8") as ff:
        ff.write("yup")  # signals test to terminate run
    while True:
        time.sleep(0.1)


output_then_hang_job = define_asset_job(
    name="output_then_hang_job",
    selection=[output_then_hang_asset],
)


@op
def my_op():
    return 1


@op(required_resource_keys={"hanging_asset_resource"})
def hanging_op(context, my_op):
    with open(context.resources.hanging_asset_resource, "w", encoding="utf8") as ff:
        ff.write("yup")

    while True:
        time.sleep(0.1)


@op
def never_runs_op(hanging_op):
    pass


@graph
def hanging_graph():
    return never_runs_op(hanging_op(my_op()))


hanging_graph_asset = AssetsDefinition.from_graph(hanging_graph)


@asset(io_manager_key="dummy_io_manager")
def downstream_asset(hanging_graph):
    return 1


hanging_graph_asset_job = define_asset_job(
    name="hanging_graph_asset_job",
    selection=[hanging_graph_asset, downstream_asset],
)


@asset
def asset_one():
    return 1


@asset
def asset_two(asset_one):
    return asset_one + 1


two_assets_job = define_asset_job(name="two_assets_job", selection=[asset_one, asset_two])


unexecutable_asset = external_asset_from_spec(AssetSpec("unexecutable_asset"))


@asset
def executable_asset(unexecutable_asset) -> None:
    pass


executable_test_job = define_asset_job(name="executable_test_job", selection=[executable_asset])

static_partitions_def = StaticPartitionsDefinition(["a", "b", "c", "d", "e", "f"])


@asset(partitions_def=static_partitions_def)
def upstream_static_partitioned_asset():
    return 1


@asset(partitions_def=static_partitions_def)
def middle_static_partitioned_asset_1(upstream_static_partitioned_asset):
    return 1


@asset(partitions_def=static_partitions_def)
def middle_static_partitioned_asset_2(upstream_static_partitioned_asset):
    return 1


@asset(partitions_def=static_partitions_def)
def downstream_static_partitioned_asset(
    middle_static_partitioned_asset_1, middle_static_partitioned_asset_2
):
    assert middle_static_partitioned_asset_1
    assert middle_static_partitioned_asset_2


static_partitioned_assets_job = define_asset_job(
    "static_partitioned_assets_job",
    AssetSelection.assets(upstream_static_partitioned_asset).downstream(),
)


@asset(partitions_def=DynamicPartitionsDefinition(name="foo"))
def upstream_dynamic_partitioned_asset():
    return 1


@asset(partitions_def=DynamicPartitionsDefinition(name="foo"))
def downstream_dynamic_partitioned_asset(
    upstream_dynamic_partitioned_asset,
):
    assert upstream_dynamic_partitioned_asset


dynamic_partitioned_assets_job = define_asset_job(
    "dynamic_partitioned_assets_job",
    selection=[upstream_dynamic_partitioned_asset, downstream_dynamic_partitioned_asset],
)


@static_partitioned_config(partition_keys=["1", "2", "3", "4", "5"])
def my_static_partitioned_config(_partition_key: str):
    return {}


@job(config=my_static_partitioned_config)
def static_partitioned_job():
    my_op()


hourly_partition = HourlyPartitionsDefinition(start_date="2021-05-05-01:00")


@daily_partitioned_config(start_date=datetime.datetime(2022, 5, 1), minute_offset=15)
def my_daily_partitioned_config(_start, _end):
    return {}


@job(config=my_daily_partitioned_config)
def daily_partitioned_job():
    my_op()


@asset(partitions_def=hourly_partition)
def upstream_time_partitioned_asset():
    return 1


@asset(
    partitions_def=hourly_partition,
    ins={
        "upstream_time_partitioned_asset": AssetIn(partition_mapping=TimeWindowPartitionMapping())
    },
)
def downstream_time_partitioned_asset(
    upstream_time_partitioned_asset,
):
    return upstream_time_partitioned_asset + 1


time_partitioned_assets_job = define_asset_job(
    "time_partitioned_assets_job",
    [upstream_time_partitioned_asset, downstream_time_partitioned_asset],
)


@asset
def unpartitioned_upstream_of_partitioned():
    return 1


@asset(partitions_def=DailyPartitionsDefinition("2023-01-01"))
def upstream_daily_partitioned_asset(unpartitioned_upstream_of_partitioned):
    return unpartitioned_upstream_of_partitioned


@asset(partitions_def=WeeklyPartitionsDefinition("2023-01-01"))
def downstream_weekly_partitioned_asset(
    upstream_daily_partitioned_asset,
):
    return upstream_daily_partitioned_asset + 1


@asset(partitions_def=StaticPartitionsDefinition(["a", "b", "c", "d"]))
def yield_partition_materialization():
    yield Output(5)


partition_materialization_job = define_asset_job(
    "partition_materialization_job",
    selection=[yield_partition_materialization],
)


@asset(partitions_def=StaticPartitionsDefinition(["a", "b", "c", "d"]))
def fail_partition_materialization(context):
    if context.run.tags.get("fail") == "true":
        raise Exception("fail_partition_materialization")
    yield Output(5)


fail_partition_materialization_job = define_asset_job(
    "fail_partition_materialization_job",
    selection=[fail_partition_materialization],
)


@asset(
    partitions_def=StaticPartitionsDefinition(["a", "b", "c", "d"]),
    io_manager_key="dummy_io_manager",
    required_resource_keys={"hanging_asset_resource"},
)
def hanging_partition_asset(context):
    with open(context.resources.hanging_asset_resource, "w", encoding="utf8") as ff:
        ff.write("yup")

    while True:
        time.sleep(0.1)


hanging_partition_asset_job = define_asset_job(
    "hanging_partition_asset_job",
    selection=[hanging_partition_asset],
)


@asset
def asset_yields_observation():
    yield AssetObservation(asset_key=AssetKey("asset_yields_observation"), metadata={"text": "FOO"})
    yield AssetObservation(asset_key=AssetKey("asset_yields_observation"), metadata={"text": "BAR"})
    yield AssetMaterialization(asset_key=AssetKey("asset_yields_observation"))
    yield Output(5)


observation_job = define_asset_job(
    "observation_job",
    selection=[asset_yields_observation],
)


@op
def op_1():
    return 1


@op
def op_2():
    return 2


@job
def two_ins_job():
    @op
    def op_with_2_ins(in_1, in_2):
        return in_1 + in_2

    op_with_2_ins(op_1(), op_2())


@job
def nested_job():
    @op
    def adder(num1: int, num2: int):
        return num1 + num2

    @op
    def plus_one(num: int):
        return num + 1

    @graph
    def subgraph():
        return plus_one(adder(op_1(), op_2()))

    plus_one(subgraph())


@job
def req_config_job():
    @op(config_schema={"foo": str})
    def the_op():
        pass

    the_op()


@asset(owners=["user@dagsterlabs.com", "team:team1"])
def asset_1():
    yield Output(3)


@asset(deps=[AssetKey("asset_1")])
def asset_2():
    raise Exception("foo")


@asset(deps=[AssetKey("asset_2")])
def asset_3():
    yield Output(7)


failure_assets_job = define_asset_job("failure_assets_job", [asset_1, asset_2, asset_3])


@asset
def foo(context: AssetExecutionContext):
    assert context.job_def.asset_selection_data is not None
    return 5


@asset
def bar(context: AssetExecutionContext):
    assert context.job_def.asset_selection_data is not None
    return 10


@asset
def foo_bar(context: AssetExecutionContext, foo, bar):
    assert context.job_def.asset_selection_data is not None
    return foo + bar


@asset
def baz(context: AssetExecutionContext, foo_bar):
    assert context.job_def.asset_selection_data is not None
    return foo_bar


@asset
def unconnected(context: AssetExecutionContext):
    assert context.job_def.asset_selection_data is not None


foo_job = define_asset_job("foo_job", [foo, bar, foo_bar, baz, unconnected])


@asset(group_name="group_1")
def grouped_asset_1():
    return 1


@asset(group_name="group_1")
def grouped_asset_2():
    return 1


@asset
def ungrouped_asset_3():
    return 1


@asset(group_name="group_2")
def grouped_asset_4():
    return 1


@asset
def ungrouped_asset_5():
    return 1


@multi_asset(outs={"int_asset": AssetOut(), "str_asset": AssetOut()})
def typed_multi_asset() -> Tuple[int, str]:
    return (1, "yay")


@asset
def typed_asset(int_asset) -> int:
    return int_asset


@asset
def untyped_asset(typed_asset):
    return typed_asset


@asset(deps=[AssetKey("diamond_source")])
def fresh_diamond_top():
    return 1


@asset
def fresh_diamond_left(fresh_diamond_top):
    return fresh_diamond_top + 1


@asset
def fresh_diamond_right(fresh_diamond_top):
    return fresh_diamond_top + 1


@asset(
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=30),
    auto_materialize_policy=AutoMaterializePolicy.lazy(),
)
def fresh_diamond_bottom(fresh_diamond_left, fresh_diamond_right):
    return fresh_diamond_left + fresh_diamond_right


@multi_asset(
    specs=[
        AssetSpec(key="first_kinds_key", kinds={"python", "airflow"}),
        AssetSpec(key="second_kinds_key", kinds={"python"}),
    ],
)
def multi_asset_with_kinds():
    return 1


@multi_asset(
    specs=[
        AssetSpec(key="third_kinds_key", tags={"dagster/storage_kind": "snowflake"}),
        AssetSpec(
            key="fourth_kinds_key",
        ),
    ],
    compute_kind="python",
)
def asset_with_compute_storage_kinds():
    return 1


@asset(automation_condition=AutomationCondition.eager())
def asset_with_automation_condition() -> None: ...


class MyAutomationCondition(AutomationCondition):
    @property
    def name(self) -> str:
        return "some_custom_name"

    def evaluate(self): ...


@asset(automation_condition=MyAutomationCondition().since_last_handled())
def asset_with_custom_automation_condition() -> None: ...


fresh_diamond_assets_job = define_asset_job(
    "fresh_diamond_assets_job", AssetSelection.assets(fresh_diamond_bottom).upstream()
)

multipartitions_def = MultiPartitionsDefinition(
    {
        "date": DailyPartitionsDefinition(start_date="2022-01-01"),
        "ab": StaticPartitionsDefinition(["a", "b", "c"]),
    }
)


@asset(partitions_def=multipartitions_def)
def multipartitions_1():
    return 1


@asset(partitions_def=multipartitions_def)
def multipartitions_2(multipartitions_1):
    return multipartitions_1


@asset(partitions_def=multipartitions_def)
def multipartitions_fail(context):
    if context.run.tags.get("fail") == "true":
        raise Exception("multipartitions_fail")
    return 1


multi_partitions_job = define_asset_job(
    "multipartitions_job", AssetSelection.assets(multipartitions_1, multipartitions_2)
)


no_partitions_multipartitions_def = MultiPartitionsDefinition(
    {
        "a": StaticPartitionsDefinition([]),
        "b": StaticPartitionsDefinition([]),
    }
)


@asset(partitions_def=no_partitions_multipartitions_def)
def no_multipartitions_1():
    return 1


dynamic_in_multipartitions_def = MultiPartitionsDefinition(
    {
        "dynamic": DynamicPartitionsDefinition(name="dynamic"),
        "static": StaticPartitionsDefinition(["a", "b", "c"]),
    }
)

no_multi_partitions_job = define_asset_job(
    "no_multipartitions_job", AssetSelection.assets(no_multipartitions_1)
)

multi_partitions_fail_job = define_asset_job(
    "multipartitions_fail_job", AssetSelection.assets(multipartitions_fail)
)


@asset(partitions_def=dynamic_in_multipartitions_def)
def dynamic_in_multipartitions_success():
    return 1


@asset(partitions_def=dynamic_in_multipartitions_def)
def dynamic_in_multipartitions_fail(context, dynamic_in_multipartitions_success):
    raise Exception("oops")


dynamic_in_multipartitions_success_job = define_asset_job(
    "dynamic_in_multipartitions_success_job",
    AssetSelection.assets(dynamic_in_multipartitions_success, dynamic_in_multipartitions_fail),
)


@asset(
    partitions_def=DailyPartitionsDefinition("2023-01-01"),
    backfill_policy=BackfillPolicy.single_run(),
)
def single_run_backfill_policy_asset(context):
    pass


@asset(
    partitions_def=DailyPartitionsDefinition("2023-01-03"),
    backfill_policy=BackfillPolicy.multi_run(10),
)
def multi_run_backfill_policy_asset(context):
    pass


named_groups_job = define_asset_job(
    "named_groups_job",
    [
        grouped_asset_1,
        grouped_asset_2,
        ungrouped_asset_3,
        grouped_asset_4,
        ungrouped_asset_5,
    ],
)


@repository
def empty_repo():
    return []


typed_assets_job = define_asset_job(
    "typed_assets",
    AssetSelection.assets(typed_multi_asset, typed_asset, untyped_asset),
)


@schedule(cron_schedule="* * * * *", job=typed_assets_job)
def asset_job_schedule():
    return {}


@asset_check(asset=asset_1, description="asset_1 check", blocking=True, additional_deps=[asset_two])
def my_check(asset_1):
    return AssetCheckResult(
        passed=True,
        metadata={
            "foo": "bar",
            "baz": "quux",
        },
    )


@asset(check_specs=[AssetCheckSpec(asset="check_in_op_asset", name="my_check")])
def check_in_op_asset():
    yield Output(1)
    yield AssetCheckResult(passed=True)


asset_check_job = define_asset_job("asset_check_job", [asset_1, check_in_op_asset])


@multi_asset(
    outs={
        "one": AssetOut(key="one", is_required=False),
        "two": AssetOut(key="two", is_required=False),
    },
    check_specs=[
        AssetCheckSpec("my_check", asset="one"),
        AssetCheckSpec("my_other_check", asset="one"),
    ],
    can_subset=True,
)
def subsettable_checked_multi_asset(context: OpExecutionContext):
    if AssetKey("one") in context.selected_asset_keys:
        yield Output(1, output_name="one")
    if AssetKey("two") in context.selected_asset_keys:
        yield Output(1, output_name="two")
    if AssetCheckKey(AssetKey("one"), "my_check") in context.selected_asset_check_keys:
        yield AssetCheckResult(check_name="my_check", passed=True)
    if AssetCheckKey(AssetKey("one"), "my_other_check") in context.selected_asset_check_keys:
        yield AssetCheckResult(check_name="my_other_check", passed=True)


checked_multi_asset_job = define_asset_job(
    "checked_multi_asset_job", AssetSelection.assets(subsettable_checked_multi_asset)
)


# These are defined separately because the dict repo does not handle unresolved asset jobs
def define_asset_jobs() -> Sequence[UnresolvedAssetJobDefinition]:
    return [
        asset_check_job,
        checked_multi_asset_job,
        dynamic_in_multipartitions_success_job,
        dynamic_partitioned_assets_job,
        executable_test_job,
        fail_partition_materialization_job,
        failure_assets_job,
        foo_job,
        fresh_diamond_assets_job,
        hanging_graph_asset_job,
        hanging_job,
        hanging_partition_asset_job,
        integers_asset_job,
        output_then_hang_job,
        multi_partitions_fail_job,
        multi_partitions_job,
        named_groups_job,
        no_multi_partitions_job,
        observation_job,
        partition_materialization_job,
        static_partitioned_assets_job,
        time_partitioned_assets_job,
        two_assets_job,
        typed_assets_job,
    ]


def define_standard_jobs() -> Sequence[JobDefinition]:
    return [
        asset_tag_job,
        basic_job,
        chained_failure_job,
        composed_graph.to_job(),
        composites_job,
        config_with_map,
        csv_hello_world,
        csv_hello_world_df_input,
        csv_hello_world_two,
        csv_hello_world_with_expectations,
        daily_partitioned_job,
        dynamic_job,
        eventually_successful,
        hard_failer,
        hello_world_with_tags,
        infinite_loop_job,
        integers,
        job_with_default_config,
        job_with_enum_config,
        job_with_expectations,
        job_with_input_output_metadata,
        job_with_invalid_definition_error,
        job_with_list,
        loggers_job,
        materialization_job,
        more_complicated_config,
        more_complicated_nested_config,
        multi_asset_job,
        naughty_programmer_job,
        nested_job,
        no_config_chain_job,
        no_config_job,
        noop_job,
        partitioned_asset_job,
        req_config_job,
        required_resource_config_job,
        required_resource_job,
        retry_multi_input_early_terminate_job,
        retry_multi_output_job,
        retry_resource_job,
        scalar_output_job,
        simple_graph.to_job("simple_job_a"),
        simple_graph.to_job("simple_job_b"),
        single_asset_job,
        spew_job,
        static_partitioned_job,
        tagged_job,
        two_ins_job,
    ]


def define_assets():
    return [
        asset_one,
        asset_two,
        untyped_asset,
        typed_asset,
        typed_multi_asset,
        multipartitions_1,
        multipartitions_2,
        no_multipartitions_1,
        multipartitions_fail,
        dynamic_in_multipartitions_success,
        dynamic_in_multipartitions_fail,
        SourceAsset("diamond_source"),
        fresh_diamond_top,
        fresh_diamond_left,
        fresh_diamond_right,
        fresh_diamond_bottom,
        integers_asset,
        upstream_daily_partitioned_asset,
        downstream_weekly_partitioned_asset,
        unpartitioned_upstream_of_partitioned,
        upstream_static_partitioned_asset,
        middle_static_partitioned_asset_1,
        middle_static_partitioned_asset_2,
        downstream_static_partitioned_asset,
        first_asset,
        hanging_asset,
        never_runs_asset,
        dummy_source_asset,
        hanging_partition_asset,
        hanging_graph_asset,
        output_then_hang_asset,
        downstream_asset,
        subsettable_checked_multi_asset,
        check_in_op_asset,
        single_run_backfill_policy_asset,
        multi_run_backfill_policy_asset,
        executable_asset,
        unexecutable_asset,
        upstream_dynamic_partitioned_asset,
        downstream_dynamic_partitioned_asset,
        upstream_time_partitioned_asset,
        downstream_time_partitioned_asset,
        yield_partition_materialization,
        fail_partition_materialization,
        asset_yields_observation,
        asset_1,
        asset_2,
        asset_3,
        foo,
        bar,
        foo_bar,
        baz,
        unconnected,
        grouped_asset_1,
        grouped_asset_2,
        ungrouped_asset_3,
        grouped_asset_4,
        ungrouped_asset_5,
        multi_asset_with_kinds,
        asset_with_compute_storage_kinds,
        asset_with_automation_condition,
        asset_with_custom_automation_condition,
    ]


def define_resources():
    return {
        "dummy_io_manager": IOManagerDefinition.hardcoded_io_manager(DummyIOManager()),
        "hanging_asset_resource": hanging_asset_resource,
    }


def define_asset_checks():
    return [
        my_check,
    ]


asset_jobs = define_asset_jobs()
asset_job_names = [job.name for job in asset_jobs]

test_repo = Definitions(
    assets=define_assets(),
    asset_checks=define_asset_checks(),
    jobs=[*asset_jobs, *define_standard_jobs()],
    schedules=define_schedules(),
    sensors=define_sensors(),
    resources=define_resources(),
    executor=in_process_executor,
).get_repository_def()

# Many tests reference the "test_repo" name directly, so we override the default
# SINGLETON_REPOSITORY NAME. This should be removed in a followup PR when references to "test_repo"
# are removed.
test_repo._name = "test_repo"  # noqa: SLF001


def _targets_asset_job(instigator: Union[ScheduleDefinition, SensorDefinition]) -> bool:
    try:
        return instigator.job_name in asset_job_names or instigator.has_anonymous_job
    except DagsterInvalidDefinitionError:  # thrown when `job_name` is invalid
        return False


# asset jobs are incompatible with dict repository so we exclude them and any schedules/sensors that target them
@repository(default_executor_def=in_process_executor)
def test_dict_repo():
    return {
        "jobs": {job.name: job for job in define_standard_jobs()},
        "schedules": {
            schedule.name: schedule
            for schedule in define_schedules()
            if not _targets_asset_job(schedule)
        },
        "sensors": {
            sensor.name: sensor for sensor in define_sensors() if not _targets_asset_job(sensor)
        },
    }
