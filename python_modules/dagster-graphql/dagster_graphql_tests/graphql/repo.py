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
from typing import List, Tuple

from dagster_graphql.test.utils import (
    define_out_of_process_context,
    infer_pipeline_selector,
    main_repo_location_name,
    main_repo_name,
)

from dagster import (
    Any,
    AssetKey,
    AssetMaterialization,
    AssetObservation,
    AssetOut,
    AssetSelection,
    AssetsDefinition,
    Bool,
    DagsterInstance,
    DefaultScheduleStatus,
    DefaultSensorStatus,
    DynamicOut,
    DynamicOutput,
    Enum,
    EnumValue,
    ExpectationResult,
    Field,
    HourlyPartitionsDefinition,
    IOManager,
    IOManagerDefinition,
    In,
    Int,
    Map,
    MetadataEntry,
    Noneable,
    Nothing,
    Out,
    Output,
    Partition,
    PythonObjectDagsterType,
    ScheduleDefinition,
    ScheduleEvaluationContext,
    SourceAsset,
    SourceHashVersionStrategy,
    StaticPartitionsDefinition,
    String,
    TableColumn,
    TableColumnConstraints,
    TableConstraints,
    TableRecord,
    TableSchema,
)
from dagster import _check as check
from dagster import (
    asset,
    dagster_type_loader,
    dagster_type_materializer,
    daily_partitioned_config,
    define_asset_job,
    graph,
    job,
    logger,
    multi_asset,
    op,
    repository,
    resource,
    schedule,
    static_partitioned_config,
    usable_as_dagster_type,
)
from dagster._core.definitions.decorators.sensor_decorator import sensor
from dagster._core.definitions.executor_definition import in_process_executor
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.definitions.multi_dimensional_partitions import MultiPartitionsDefinition
from dagster._core.definitions.reconstruct import ReconstructableRepository
from dagster._core.definitions.sensor_definition import RunRequest, SkipReason
from dagster._core.log_manager import coerce_valid_log_level
from dagster._core.storage.fs_io_manager import fs_io_manager
from dagster._core.storage.pipeline_run import DagsterRunStatus, RunsFilter
from dagster._core.storage.tags import RESUME_RETRY_TAG
from dagster._core.test_utils import default_mode_def_for_test, today_at_midnight
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster._core.workspace.load_target import PythonFileTarget
from dagster._legacy import (
    AssetGroup,
    InputDefinition,
    Materialization,
    ModeDefinition,
    OpExecutionContext,
    OutputDefinition,
    PartitionSetDefinition,
    PresetDefinition,
    build_assets_job,
    daily_schedule,
    hourly_schedule,
    monthly_schedule,
    pipeline,
    weekly_schedule,
)
from dagster._seven import get_system_temp_directory
from dagster._utils import file_relative_path, segfault

LONG_INT = 2875972244  # 32b unsigned, > 32b signed


@dagster_type_loader(String)
def df_input_schema(_context, path):
    with open(path, "r", encoding="utf8") as fd:
        return [OrderedDict(sorted(x.items(), key=lambda x: x[0])) for x in csv.DictReader(fd)]


@dagster_type_materializer(String)
def df_output_schema(_context, path, value):
    with open(path, "w", encoding="utf8") as fd:
        writer = csv.DictWriter(fd, fieldnames=value[0].keys())
        writer.writeheader()
        writer.writerows(rowdicts=value)

    return AssetMaterialization.file(path)


PoorMansDataFrame = PythonObjectDagsterType(
    python_type=list,
    name="PoorMansDataFrame",
    loader=df_input_schema,
    materializer=df_output_schema,
)


@contextmanager
def define_test_out_of_process_context(instance):
    check.inst_param(instance, "instance", DagsterInstance)
    with define_out_of_process_context(__file__, main_repo_name(), instance) as context:
        yield context


def create_main_recon_repo():
    return ReconstructableRepository.for_file(__file__, main_repo_name())


@contextmanager
def get_main_workspace(instance):
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
def get_main_external_repo(instance):
    with get_main_workspace(instance) as workspace:
        location = workspace.get_repository_location(main_repo_location_name())
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


def csv_hello_world_solids_config():
    return {
        "solids": {"sum_op": {"inputs": {"num": file_relative_path(__file__, "../data/num.csv")}}}
    }


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


def lineage_solid_factory(solid_name_prefix, key, partitions=None):
    @op(
        name=f"{solid_name_prefix}_{key}",
        out=Out(asset_key=AssetKey(key), asset_partitions=partitions),
    )
    def _op(_, _in1):
        yield Output(1)

    return _op


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
def asset_lineage_job():
    lineage_solid_factory("alp", "b")(lineage_solid_factory("alp", "a")(noop_op()))


@job
def partitioned_asset_lineage_job():
    lineage_solid_factory("palp", "b", set("1"))(
        lineage_solid_factory("palp", "a", set("1"))(noop_op())
    )


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
    def a_op_with_three_field_config(_context):
        return None

    noop_op()
    a_op_with_three_field_config()


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
    def a_op_with_map_config(_context):
        return None

    noop_op()
    a_op_with_map_config()


@job
def more_complicated_nested_config():
    @op(
        name="a_op_with_multilayered_config",
        ins={},
        out={},
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
    )
    def a_op_with_multilayered_config(_):
        return None

    a_op_with_multilayered_config()


@pipeline(
    mode_defs=[default_mode_def_for_test],
    preset_defs=[
        PresetDefinition.from_files(
            name="prod",
            config_files=[
                file_relative_path(__file__, "../environments/csv_hello_world_prod.yaml")
            ],
        ),
        PresetDefinition.from_files(
            name="test",
            config_files=[
                file_relative_path(__file__, "../environments/csv_hello_world_test.yaml")
            ],
        ),
        PresetDefinition(
            name="test_inline",
            run_config={
                "solids": {
                    "sum_op": {"inputs": {"num": file_relative_path(__file__, "../data/num.csv")}}
                }
            },
        ),
    ],
)
def csv_hello_world():
    sum_sq_op(sum_df=sum_op())


@pipeline(mode_defs=[default_mode_def_for_test])
def csv_hello_world_with_expectations():
    ss = sum_op()
    sum_sq_op(sum_df=ss)
    df_expectations_op(sum_df=ss)


@pipeline(mode_defs=[default_mode_def_for_test])
def csv_hello_world_two():
    sum_op()


@op
def op_that_gets_tags(context):
    return context.run.tags


@pipeline(mode_defs=[default_mode_def_for_test], tags={"tag_key": "tag_value"})
def hello_world_with_tags():
    op_that_gets_tags()


@op(name="solid_with_list", ins={}, out={}, config_schema=[int])
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


@pipeline(mode_defs=[default_mode_def_for_test])
def csv_hello_world_df_input():
    sum_sq_op(sum_op())


@pipeline(mode_defs=[default_mode_def_for_test])
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
    def return_hello_world(_):
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
                raise Exception("bad programmer, bad")
            except Exception as e:
                raise Exception("Outer exception") from e
        except Exception as e:
            raise Exception("Even more outer exception") from e

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
        out=Out(Int),
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


@pipeline(
    mode_defs=[
        ModeDefinition(
            name="add_mode",
            resource_defs={"op": adder_resource},
            description="Mode that adds things",
        ),
        ModeDefinition(
            name="mult_mode",
            resource_defs={"op": multer_resource},
            description="Mode that multiplies things",
        ),
        ModeDefinition(
            name="double_adder",
            resource_defs={"op": double_adder_resource},
            description="Mode that adds two numbers to thing",
        ),
    ],
    preset_defs=[PresetDefinition.from_files("add", mode="add_mode")],
)
def multi_mode_with_resources():
    @op(required_resource_keys={"op"})
    def apply_to_three(context):
        return context.resources.op(3)

    apply_to_three()


@resource(config_schema=Field(Int, is_required=False))
def req_resource(_):
    return 1


@job(resource_defs={"R1": req_resource})
def required_resource_job():
    @op(required_resource_keys={"R1"})
    def op_with_required_resource(_):
        return 1

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

        def log(self, lvl, msg, *args, **kwargs):  # pylint: disable=arguments-differ
            msg = self.prefix + msg
            super(BarLogger, self).log(lvl, msg, *args, **kwargs)

    logger_ = BarLogger("bar", init_context.logger_config["prefix"])
    logger_.setLevel(coerce_valid_log_level(init_context.logger_config["log_level"]))


@pipeline(
    mode_defs=[
        ModeDefinition(
            name="foo_mode",
            resource_defs={"io_manager": fs_io_manager},
            logger_defs={"foo": foo_logger},
            description="Mode with foo logger",
        ),
        ModeDefinition(
            name="bar_mode",
            resource_defs={"io_manager": fs_io_manager},
            logger_defs={"bar": bar_logger},
            description="Mode with bar logger",
        ),
        ModeDefinition(
            name="foobar_mode",
            resource_defs={"io_manager": fs_io_manager},
            logger_defs={"foo": foo_logger, "bar": bar_logger},
            description="Mode with multiple loggers",
        ),
    ]
)
def multi_mode_with_loggers():
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

    @graph(input_defs=[InputDefinition("num", Int)], output_defs=[OutputDefinition(Int)])
    def add_two(num):
        return add_one.alias("adder_2")(add_one.alias("adder_1")(num))

    @graph(input_defs=[InputDefinition("num", Int)], output_defs=[OutputDefinition(Int)])
    def add_four(num):
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
            metadata_entries=[
                MetadataEntry("text", value="text is cool"),
                MetadataEntry("url", value=MetadataValue.url("https://bigty.pe/neato")),
                MetadataEntry("path", value=MetadataValue.path("/tmp/awesome")),
                MetadataEntry("json", value={"is_dope": True}),
                MetadataEntry("python class", value=MetadataValue.python_artifact(MetadataEntry)),
                MetadataEntry(
                    "python function",
                    value=MetadataValue.python_artifact(file_relative_path),
                ),
                MetadataEntry("float", value=1.2),
                MetadataEntry("int", value=1),
                MetadataEntry("float NaN", value=float("nan")),
                MetadataEntry("long int", value=LONG_INT),
                MetadataEntry("pipeline run", value=MetadataValue.dagster_run("fake_run_id")),
                MetadataEntry("my asset", value=AssetKey("my_asset")),
                MetadataEntry(
                    "table",
                    value=MetadataValue.table(
                        records=[
                            TableRecord(foo=1, bar=2),
                            TableRecord(foo=3, bar=4),
                        ],
                    ),
                ),
                MetadataEntry(
                    "table_schema",
                    value=TableSchema(
                        columns=[
                            TableColumn(
                                name="foo",
                                type="integer",
                                constraints=TableColumnConstraints(unique=True),
                            ),
                            TableColumn(name="bar", type="string"),
                        ],
                        constraints=TableConstraints(
                            other=["some constraint"],
                        ),
                    ),
                ),
            ],
        )
        yield Output(None)

    materialize()


@job
def spew_job():
    @op
    def spew(_):
        print("HELLO WORLD")  # pylint: disable=print-call

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
        "io_manager": fs_io_manager,
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


@job
def hard_failer():
    @op(
        config_schema={"fail": Field(Bool, is_required=False, default_value=False)},
        out=Out(Int),
    )
    def hard_fail_or_0(context):
        if context.op_config["fail"]:
            segfault()
        return 0

    @op(
        ins={"n": In(Int)},
    )
    def increment(_, n):
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
def will_fail(context, num):  # pylint: disable=unused-argument
    assert context.resources.b == "B"
    raise Exception("fail")


@job(
    resource_defs={
        "a": resource_a,
        "b": resource_b,
        "io_manager": fs_io_manager,
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
def can_fail(context, inp):  # pylint: disable=unused-argument
    if context.op_config["fail"]:
        raise Exception("blah")

    yield Output("okay perfect", "start_fail")


@op(
    out={"success": Out(str, is_required=False), "skip": Out(str, is_required=False)},
)
def multi(_):
    yield Output("okay perfect", "success")


@op
def passthrough(_, value):
    return value


@op(ins={"start": In(Nothing)}, out={})
def no_output(_):
    yield ExpectationResult(True)


@pipeline(mode_defs=[default_mode_def_for_test])
def retry_multi_output_job():
    multi_success, multi_skip = multi()
    fail, skip = can_fail(multi_success)
    no_output.alias("child_multi_skip")(multi_skip)
    no_output.alias("child_skip")(skip)
    no_output.alias("grandchild_fail")(passthrough.alias("child_fail")(fail))


@pipeline(tags={"foo": "bar"}, mode_defs=[default_mode_def_for_test])
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
        print("Disabling GC")  # pylint: disable=print-call
        gc.disable()
        yield
    finally:
        print("Re-enabling GC")  # pylint: disable=print-call
        gc.enable()


@job(resource_defs={"io_manager": fs_io_manager, "disable_gc": disable_gc})
def retry_multi_input_early_terminate_job():
    @op(out=Out(Int))
    def return_one():
        return 1

    @op(
        config_schema={"wait_to_terminate": bool},
        ins={"one": In(Int)},
        out=Out(Int),
        required_resource_keys={"disable_gc"},
    )
    def get_input_one(context, one):
        if context.op_config["wait_to_terminate"]:
            while True:
                time.sleep(0.1)
        return one

    @op(
        config_schema={"wait_to_terminate": bool},
        ins={"one": In(Int)},
        out=Out(Int),
        required_resource_keys={"disable_gc"},
    )
    def get_input_two(context, one):
        if context.op_config["wait_to_terminate"]:
            while True:
                time.sleep(0.1)
        return one

    @op(
        ins={"input_one": In(Int), "input_two": In(Int)},
        out=Out(Int),
    )
    def sum_inputs(input_one, input_two):
        return input_one + input_two

    step_one = return_one()
    sum_inputs(input_one=get_input_one(step_one), input_two=get_input_two(step_one))


@pipeline(mode_defs=[default_mode_def_for_test])
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

    # pylint: disable=no-member
    multiply_by_two.alias("double_total")(
        sum_numbers(
            emit()
            .map(
                lambda n: multiply_by_two(multiply_inputs(n, emit_ten())),
            )
            .collect(),
        )
    )


def get_retry_multi_execution_params(graphql_context, should_fail, retry_id=None):
    selector = infer_pipeline_selector(graphql_context, "retry_multi_output_job")
    return {
        "mode": "default",
        "selector": selector,
        "runConfigData": {
            "solids": {"can_fail": {"config": {"fail": should_fail}}},
        },
        "executionMetadata": {
            "rootRunId": retry_id,
            "parentRunId": retry_id,
            "tags": ([{"key": RESUME_RETRY_TAG, "value": "true"}] if retry_id else []),
        },
    }


def last_empty_partition(context, partition_set_def):
    check.inst_param(context, "context", ScheduleEvaluationContext)
    partition_set_def = check.inst_param(
        partition_set_def, "partition_set_def", PartitionSetDefinition
    )

    partitions = partition_set_def.get_partitions(context.scheduled_execution_time)
    if not partitions:
        return None
    selected = None
    for partition in reversed(partitions):
        filters = RunsFilter.for_partition(partition_set_def, partition)
        matching = context.instance.get_runs(filters)
        if not any(run.status == DagsterRunStatus.SUCCESS for run in matching):
            selected = partition
            break
    return selected


def define_schedules():
    integer_partition_set = PartitionSetDefinition(
        name="scheduled_integer_partitions",
        pipeline_name="no_config_job",
        partition_fn=lambda: [Partition(x) for x in range(1, 10)],
        tags_fn_for_partition=lambda _partition: {"test": "1234"},
    )

    no_config_pipeline_hourly_schedule = ScheduleDefinition(
        name="no_config_job_hourly_schedule",
        cron_schedule="0 0 * * *",
        job_name="no_config_job",
    )

    no_config_pipeline_hourly_schedule_with_config_fn = ScheduleDefinition(
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

    partition_based = integer_partition_set.create_schedule_definition(
        schedule_name="partition_based",
        cron_schedule="0 0 * * *",
        partition_selector=last_empty_partition,
    )

    @daily_schedule(
        pipeline_name="no_config_job",
        start_date=today_at_midnight().subtract(days=1),
        execution_time=(datetime.datetime.now() + datetime.timedelta(hours=2)).time(),
    )
    def partition_based_decorator(_date):
        return {}

    @daily_schedule(
        pipeline_name="no_config_job",
        start_date=today_at_midnight().subtract(days=1),
        execution_time=(datetime.datetime.now() + datetime.timedelta(hours=2)).time(),
        default_status=DefaultScheduleStatus.RUNNING,
    )
    def running_in_code_schedule(_date):
        return {}

    @daily_schedule(
        pipeline_name="multi_mode_with_loggers",
        start_date=today_at_midnight().subtract(days=1),
        execution_time=(datetime.datetime.now() + datetime.timedelta(hours=2)).time(),
        mode="foo_mode",
    )
    def partition_based_multi_mode_decorator(_date):
        return {}

    @hourly_schedule(
        pipeline_name="no_config_chain_job",
        start_date=today_at_midnight().subtract(days=1),
        execution_time=(datetime.datetime.now() + datetime.timedelta(hours=2)).time(),
        solid_selection=["return_foo"],
    )
    def solid_selection_hourly_decorator(_date):
        return {}

    @daily_schedule(
        pipeline_name="no_config_chain_job",
        start_date=today_at_midnight().subtract(days=2),
        execution_time=(datetime.datetime.now() + datetime.timedelta(hours=3)).time(),
        solid_selection=["return_foo"],
    )
    def solid_selection_daily_decorator(_date):
        return {}

    @monthly_schedule(
        pipeline_name="no_config_chain_job",
        start_date=(today_at_midnight().subtract(days=100)).replace(day=1),
        execution_time=(datetime.datetime.now() + datetime.timedelta(hours=4)).time(),
        solid_selection=["return_foo"],
    )
    def solid_selection_monthly_decorator(_date):
        return {}

    @weekly_schedule(
        pipeline_name="no_config_chain_job",
        start_date=today_at_midnight().subtract(days=50),
        execution_time=(datetime.datetime.now() + datetime.timedelta(hours=5)).time(),
        solid_selection=["return_foo"],
    )
    def solid_selection_weekly_decorator(_date):
        return {}

    # Schedules for testing the user error boundary
    @daily_schedule(
        pipeline_name="no_config_job",
        start_date=today_at_midnight().subtract(days=1),
        should_execute=lambda _: asdf,  # pylint: disable=undefined-variable
    )
    def should_execute_error_schedule(_date):
        return {}

    @daily_schedule(
        pipeline_name="no_config_job",
        start_date=today_at_midnight().subtract(days=1),
        tags_fn_for_date=lambda _: asdf,  # pylint: disable=undefined-variable
    )
    def tags_error_schedule(_date):
        return {}

    @daily_schedule(
        pipeline_name="no_config_job",
        start_date=today_at_midnight().subtract(days=1),
    )
    def run_config_error_schedule(_date):
        return asdf  # pylint: disable=undefined-variable

    @daily_schedule(
        pipeline_name="no_config_job",
        start_date=today_at_midnight("US/Central") - datetime.timedelta(days=1),
        execution_timezone="US/Central",
    )
    def timezone_schedule(_date):
        return {}

    tagged_pipeline_schedule = ScheduleDefinition(
        name="tagged_job_schedule",
        cron_schedule="0 0 * * *",
        job_name="tagged_job",
    )

    tagged_pipeline_override_schedule = ScheduleDefinition(
        name="tagged_job_override_schedule",
        cron_schedule="0 0 * * *",
        job_name="tagged_job",
        tags={"foo": "notbar"},
    )

    invalid_config_schedule = ScheduleDefinition(
        name="invalid_config_schedule",
        cron_schedule="0 0 * * *",
        job_name="job_with_enum_config",
        run_config={"solids": {"takes_an_enum": {"config": "invalid"}}},
    )

    @schedule(
        job_name="nested_job",
        cron_schedule=["45 23 * * 6", "30 9 * * 0"],
    )
    def composite_cron_schedule(_context):
        return {}

    return [
        run_config_error_schedule,
        no_config_pipeline_hourly_schedule,
        no_config_pipeline_hourly_schedule_with_config_fn,
        no_config_should_execute,
        dynamic_config,
        partition_based,
        partition_based_decorator,
        partition_based_multi_mode_decorator,
        solid_selection_hourly_decorator,
        solid_selection_daily_decorator,
        solid_selection_monthly_decorator,
        solid_selection_weekly_decorator,
        should_execute_error_schedule,
        tagged_pipeline_schedule,
        tagged_pipeline_override_schedule,
        tags_error_schedule,
        timezone_schedule,
        invalid_config_schedule,
        running_in_code_schedule,
        composite_cron_schedule,
    ]


def define_partitions():
    integer_set = PartitionSetDefinition(
        name="integer_partition",
        pipeline_name="no_config_job",
        solid_selection=["return_hello"],
        mode="default",
        partition_fn=lambda: [Partition(i) for i in range(10)],
        tags_fn_for_partition=lambda partition: {"foo": partition.name},
    )

    enum_set = PartitionSetDefinition(
        name="enum_partition",
        pipeline_name="noop_job",
        partition_fn=lambda: ["one", "two", "three"],
    )

    chained_partition_set = PartitionSetDefinition(
        name="chained_integer_partition",
        pipeline_name="chained_failure_job",
        mode="default",
        partition_fn=lambda: [Partition(i) for i in range(10)],
    )

    alphabet_partition_set = PartitionSetDefinition(
        name="alpha_partition",
        pipeline_name="no_config_job",
        partition_fn=lambda: list(string.ascii_lowercase),
    )

    return [integer_set, enum_set, chained_partition_set, alphabet_partition_set]


def define_sensors():
    @sensor(job_name="no_config_job")
    def always_no_config_sensor(_):
        return RunRequest(
            run_key=None,
            tags={"test": "1234"},
        )

    @sensor(job_name="no_config_job")
    def once_no_config_sensor(_):
        return RunRequest(
            run_key="once",
            tags={"test": "1234"},
        )

    @sensor(job_name="no_config_job")
    def never_no_config_sensor(_):
        return SkipReason("never")

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

    @sensor(job_name="no_config_pipeline")
    def logging_sensor(context):
        context.log.info("hello hello")
        return SkipReason()

    return [
        always_no_config_sensor,
        once_no_config_sensor,
        never_no_config_sensor,
        multi_no_config_sensor,
        custom_interval_sensor,
        running_in_code_sensor,
        logging_sensor,
    ]


@pipeline(mode_defs=[default_mode_def_for_test])
def chained_failure_job():
    @op
    def always_succeed():
        return "hello"

    @op
    def conditionally_fail(_):
        if os.path.isfile(
            os.path.join(
                get_system_temp_directory(),
                "chained_failure_job_conditionally_fail",
            )
        ):
            raise Exception("blah")

        return "hello"

    @op
    def after_failure(_):
        return "world"

    after_failure(conditionally_fail(always_succeed()))


@job
def backcompat_materialization_job():
    @op
    def backcompat_materialize(_):
        yield Materialization(
            asset_key="all_types",
            description="a materialization with all metadata types",
            metadata_entries=[
                MetadataEntry("text", value="text is cool"),
                MetadataEntry("url", value=MetadataValue.url("https://bigty.pe/neato")),
                MetadataEntry("path", value=MetadataValue.path("/tmp/awesome")),
                MetadataEntry("json", value={"is_dope": True}),
                MetadataEntry("python class", value=MetadataValue.python_artifact(MetadataEntry)),
                MetadataEntry(
                    "python function",
                    value=MetadataValue.python_artifact(file_relative_path),
                ),
                MetadataEntry("float", value=1.2),
                MetadataEntry("int", value=1),
                MetadataEntry("float NaN", value=float("nan")),
                MetadataEntry("long int", value=LONG_INT),
                MetadataEntry("pipeline run", value=MetadataValue.pipeline_run("fake_run_id")),
                MetadataEntry("my asset", value=AssetKey("my_asset")),
            ],
        )
        yield Output(None)

    backcompat_materialize()


@graph
def simple_graph():
    noop_op()


@graph
def composed_graph():
    simple_graph()


@job(config={"ops": {"a_op_with_config": {"config": {"one": "hullo"}}}})
def job_with_default_config():
    @op(config_schema={"one": Field(String)})
    def a_solid_with_config(context):
        return context.op_config["one"]

    a_solid_with_config()


@resource(config_schema={"file": Field(String)})
def hanging_asset_resource(context):
    # Hack to allow asset to get value from run config
    return context.resource_config.get("file")


class DummyIOManager(IOManager):
    def handle_output(self, context, obj):
        pass

    def load_input(self, context):
        pass


dummy_source_asset = SourceAsset(key=AssetKey("dummy_source_asset"))


@asset
def first_asset(
    dummy_source_asset,
):  # pylint: disable=redefined-outer-name,unused-argument
    return 1


@asset(required_resource_keys={"hanging_asset_resource"})
def hanging_asset(context, first_asset):  # pylint: disable=redefined-outer-name,unused-argument
    """
    Asset that hangs forever, used to test in-progress ops.
    """
    with open(context.resources.hanging_asset_resource, "w", encoding="utf8") as ff:
        ff.write("yup")

    while True:
        time.sleep(0.1)


@asset
def never_runs_asset(
    hanging_asset,
):  # pylint: disable=redefined-outer-name,unused-argument
    pass


hanging_job = build_assets_job(
    name="hanging_job",
    source_assets=[dummy_source_asset],
    assets=[first_asset, hanging_asset, never_runs_asset],
    resource_defs={
        "io_manager": IOManagerDefinition.hardcoded_io_manager(DummyIOManager()),
        "hanging_asset_resource": hanging_asset_resource,
    },
)


@op
def my_op():
    return 1


@op(required_resource_keys={"hanging_asset_resource"})
def hanging_op(context, my_op):  # pylint: disable=unused-argument
    with open(context.resources.hanging_asset_resource, "w", encoding="utf8") as ff:
        ff.write("yup")

    while True:
        time.sleep(0.1)


@op
def never_runs_op(hanging_op):  # pylint: disable=unused-argument
    pass


@graph
def hanging_graph():
    return never_runs_op(hanging_op(my_op()))


hanging_graph_asset = AssetsDefinition.from_graph(hanging_graph)


@job(version_strategy=SourceHashVersionStrategy())
def memoization_job():
    my_op()


@asset
def downstream_asset(hanging_graph):  # pylint: disable=unused-argument
    return 1


hanging_graph_asset_job = AssetGroup(
    [hanging_graph_asset, downstream_asset],
    resource_defs={
        "hanging_asset_resource": hanging_asset_resource,
        "io_manager": IOManagerDefinition.hardcoded_io_manager(DummyIOManager()),
    },
).build_job("hanging_graph_asset_job")


@asset
def asset_one():
    return 1


@asset
def asset_two(asset_one):  # pylint: disable=redefined-outer-name,unused-argument
    return first_asset + 1


two_assets_job = build_assets_job(name="two_assets_job", assets=[asset_one, asset_two])


static_partitions_def = StaticPartitionsDefinition(["a", "b", "c", "d"])


@asset(partitions_def=static_partitions_def)
def upstream_static_partitioned_asset():
    return 1


@asset(partitions_def=static_partitions_def)
def downstream_static_partitioned_asset(
    upstream_static_partitioned_asset,
):  # pylint: disable=redefined-outer-name
    assert upstream_static_partitioned_asset


static_partitioned_assets_job = build_assets_job(
    "static_partitioned_assets_job",
    assets=[upstream_static_partitioned_asset, downstream_static_partitioned_asset],
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


@asset(partitions_def=hourly_partition)
def downstream_time_partitioned_asset(
    upstream_time_partitioned_asset,
):  # pylint: disable=redefined-outer-name
    return upstream_time_partitioned_asset + 1


time_partitioned_assets_job = build_assets_job(
    "time_partitioned_assets_job",
    [upstream_time_partitioned_asset, downstream_time_partitioned_asset],
)


@asset(partitions_def=StaticPartitionsDefinition(["a", "b", "c", "d"]))
def yield_partition_materialization():
    yield AssetMaterialization(asset_key=AssetKey("yield_partition_materialization"), partition="c")
    yield Output(5)


partition_materialization_job = build_assets_job(
    "partition_materialization_job",
    assets=[yield_partition_materialization],
    executor_def=in_process_executor,
)


@asset
def asset_yields_observation():
    yield AssetObservation(asset_key=AssetKey("asset_yields_observation"), metadata={"text": "FOO"})
    yield AssetMaterialization(asset_key=AssetKey("asset_yields_observation"))
    yield Output(5)


observation_job = build_assets_job(
    "observation_job",
    assets=[asset_yields_observation],
    executor_def=in_process_executor,
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


@asset
def asset_1():
    yield Output(3)


@asset(non_argument_deps={AssetKey("asset_1")})
def asset_2():
    raise Exception("foo")


@asset(non_argument_deps={AssetKey("asset_2")})
def asset_3():
    yield Output(7)


failure_assets_job = build_assets_job(
    "failure_assets_job", [asset_1, asset_2, asset_3], executor_def=in_process_executor
)


@asset
def foo(context):
    assert context.pipeline_def.asset_selection_data != None
    return 5


@asset
def bar(context):
    assert context.pipeline_def.asset_selection_data != None
    return 10


@asset
def foo_bar(context, foo, bar):
    assert context.pipeline_def.asset_selection_data != None
    return foo + bar


@asset
def baz(context, foo_bar):
    assert context.pipeline_def.asset_selection_data != None
    return foo_bar


@asset
def unconnected(context):
    assert context.pipeline_def.asset_selection_data != None


asset_group_job = AssetGroup([foo, bar, foo_bar, baz, unconnected]).build_job("foo_job")


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


@asset(non_argument_deps={AssetKey("diamond_source")})
def fresh_diamond_top():
    return 1


@asset
def fresh_diamond_left(fresh_diamond_top):
    return fresh_diamond_top + 1


@asset
def fresh_diamond_right(fresh_diamond_top):
    return fresh_diamond_top + 1


@asset(freshness_policy=FreshnessPolicy(maximum_lag_minutes=30))
def fresh_diamond_bottom(fresh_diamond_left, fresh_diamond_right):
    return fresh_diamond_left + fresh_diamond_right


multipartitions_def = MultiPartitionsDefinition(
    {
        "12": StaticPartitionsDefinition(["1", "2"]),
        "ab": StaticPartitionsDefinition(["a", "b"]),
    }
)


@asset(partitions_def=multipartitions_def)
def multipartitions_1():
    return 1


@asset(partitions_def=multipartitions_def)
def multipartitions_2(multipartitions_1):
    return multipartitions_1


# For now the only way to add assets to repositories is via AssetGroup
# When AssetGroup is removed, these assets should be added directly to repository_with_named_groups
named_groups_job = AssetGroup(
    [
        grouped_asset_1,
        grouped_asset_2,
        ungrouped_asset_3,
        grouped_asset_4,
        ungrouped_asset_5,
    ]
).build_job("named_groups_job")


@repository
def empty_repo():
    return []


def define_pipelines():
    return [
        asset_tag_job,
        composites_job,
        csv_hello_world_df_input,
        csv_hello_world_two,
        csv_hello_world_with_expectations,
        csv_hello_world,
        daily_partitioned_job,
        eventually_successful,
        hard_failer,
        hello_world_with_tags,
        infinite_loop_job,
        materialization_job,
        more_complicated_config,
        more_complicated_nested_config,
        config_with_map,
        multi_asset_job,
        multi_mode_with_loggers,
        multi_mode_with_resources,
        naughty_programmer_job,
        nested_job,
        no_config_chain_job,
        no_config_job,
        noop_job,
        partitioned_asset_job,
        job_with_enum_config,
        job_with_expectations,
        job_with_input_output_metadata,
        job_with_invalid_definition_error,
        job_with_list,
        required_resource_job,
        retry_multi_input_early_terminate_job,
        retry_multi_output_job,
        retry_resource_job,
        scalar_output_job,
        single_asset_job,
        spew_job,
        static_partitioned_job,
        tagged_job,
        chained_failure_job,
        dynamic_job,
        asset_lineage_job,
        partitioned_asset_lineage_job,
        backcompat_materialization_job,
        simple_graph.to_job("simple_job_a"),
        simple_graph.to_job("simple_job_b"),
        composed_graph.to_job(),
        job_with_default_config,
        hanging_job,
        two_ins_job,
        two_assets_job,
        static_partitioned_assets_job,
        time_partitioned_assets_job,
        partition_materialization_job,
        observation_job,
        failure_assets_job,
        asset_group_job,
        hanging_graph_asset_job,
        named_groups_job,
        memoization_job,
    ]


def define_asset_jobs():
    return [
        untyped_asset,
        typed_asset,
        typed_multi_asset,
        define_asset_job(
            "typed_assets",
            AssetSelection.assets(typed_multi_asset, typed_asset, untyped_asset),
        ),
        multipartitions_1,
        multipartitions_2,
        define_asset_job(
            "multipartitions_job",
            AssetSelection.assets(multipartitions_1, multipartitions_2),
            partitions_def=multipartitions_def,
        ),
        SourceAsset("diamond_source"),
        fresh_diamond_top,
        fresh_diamond_left,
        fresh_diamond_right,
        fresh_diamond_bottom,
        define_asset_job(
            "fresh_diamond_assets", AssetSelection.assets(fresh_diamond_bottom).upstream()
        ),
    ]


@repository
def test_repo():
    return (
        define_pipelines()
        + define_schedules()
        + define_sensors()
        + define_partitions()
        + define_asset_jobs()
    )


@repository
def test_dict_repo():
    return {
        "pipelines": {pipeline.name: pipeline for pipeline in define_pipelines()},
        "schedules": {schedule.name: schedule for schedule in define_schedules()},
        "sensors": {sensor.name: sensor for sensor in define_sensors()},
        "partition_sets": {
            partition_set.name: partition_set for partition_set in define_partitions()
        },
    }
