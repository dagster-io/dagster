import enum
import json
from datetime import datetime
from itertools import count
from typing import Any, Optional

import pytest
from dagster import (
    ConfigMapping,
    DagsterInstance,
    DagsterTypeCheckDidNotPass,
    DynamicOut,
    DynamicOutput,
    Enum,
    Field,
    GraphOut,
    In,
    InputMapping,
    Nothing,
    Out,
    Permissive,
    Shape,
    graph,
    input_manager,
    logger,
    op,
    resource,
    success_hook,
)
from dagster._check import CheckError
from dagster._core.definitions.graph_definition import GraphDefinition
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.partition import PartitionedConfig, StaticPartitionsDefinition
from dagster._core.definitions.time_window_partitions import DailyPartitionsDefinition, TimeWindow
from dagster._core.errors import (
    DagsterConfigMappingFunctionError,
    DagsterInvalidConfigError,
    DagsterInvalidDefinitionError,
)
from dagster._core.test_utils import instance_for_test
from dagster._loggers import json_console_logger
from dagster._time import parse_time_string


def get_ops():
    @op
    def emit_one(_):
        return 1

    @op
    def add(_, x, y):
        return x + y

    return emit_one, add


def test_top_level_inputs_execution():
    @op
    def the_op(leaf_in: int):
        return leaf_in + 1

    @graph
    def the_graph(the_in):
        return the_op(the_in)

    result = the_graph.execute_in_process(input_values={"the_in": 2})
    assert result.success
    assert result.output_value() == 3

    with pytest.raises(
        DagsterTypeCheckDidNotPass,
        match=(
            'Type check failed for step input "leaf_in" - expected type "Int". Description: Value'
            ' "bad_value" of python type "str" must be a int.'
        ),
    ):
        the_graph.execute_in_process(input_values={"the_in": "bad_value"})


def test_basic_graph():
    emit_one, add = get_ops()

    @graph
    def get_two():
        return add(emit_one(), emit_one())

    assert isinstance(get_two, GraphDefinition)

    result = get_two.execute_in_process()
    assert result.success


def test_aliased_graph():
    emit_one, add = get_ops()

    @graph
    def get_two():
        return add(emit_one(), emit_one.alias("emit_one_part_two")())

    assert isinstance(get_two, GraphDefinition)

    result = get_two.execute_in_process()
    assert result.success

    assert result.output_for_node("emit_one") == 1
    assert result.output_for_node("emit_one_part_two") == 1


def test_composite_graph():
    emit_one, add = get_ops()

    @graph
    def add_one(x):
        return add(emit_one(), x)

    @graph
    def add_two(x):
        return add(add_one(x), emit_one())

    assert isinstance(add_two, GraphDefinition)


def test_with_resources():
    @resource
    def a_resource(_):
        return "a"

    @op(required_resource_keys={"a"})
    def needs_resource(context):
        return context.resources.a

    @graph
    def my_graph():
        needs_resource()

    # proxy for "executable/job"
    my_job = my_graph.to_job(resource_defs={"a": a_resource})
    assert my_job.name == "my_graph"
    result = my_job.execute_in_process()
    assert result.success

    result = my_graph.execute_in_process(resources={"a": "foo"})
    assert result.success


def test_error_on_invalid_resource_key():
    @resource
    def test_resource():
        return "test-resource"

    @op(required_resource_keys={"test-resource"})
    def needs_resource(_):
        return ""

    @graph
    def test_graph():
        needs_resource()

    with pytest.raises(CheckError, match="test-resource"):
        test_graph.to_job(
            resource_defs={
                "test-resource": test_resource,
            }
        )


def test_config_mapping_fn():
    @resource(config_schema=str)
    def date(context) -> str:
        return context.resource_config

    @op(
        required_resource_keys={"date"},
        config_schema={"msg": str},
    )
    def do_stuff(context):
        return f"{context.op_config['msg'] } on {context.resources.date}"

    @graph
    def needs_config():
        do_stuff()

    def _mapped(val):
        return {
            "ops": {"do_stuff": {"config": {"msg": "i am here"}}},
            "resources": {"date": {"config": val["date"]}},
        }

    job = needs_config.to_job(
        resource_defs={"date": date},
        config=ConfigMapping(
            config_schema={"date": str},  # top level has to be dict
            config_fn=_mapped,
        ),
    )

    result = job.execute_in_process(run_config={"date": "6/4"})
    assert result.success
    assert result.output_for_node("do_stuff") == "i am here on 6/4"


def test_default_config():
    @resource(config_schema=str)
    def date(context) -> str:
        return context.resource_config

    @op(
        required_resource_keys={"date"},
        config_schema={"msg": str},
    )
    def do_stuff(context):
        return f"{context.op_config['msg'] } on {context.resources.date}"

    @graph
    def needs_config():
        do_stuff()

    job = needs_config.to_job(
        resource_defs={"date": date},
        config={
            "ops": {"do_stuff": {"config": {"msg": "i am here"}}},
            "resources": {"date": {"config": "6/3"}},
        },
    )

    result = job.execute_in_process()
    assert result.success
    assert result.output_for_node("do_stuff") == "i am here on 6/3"


def test_suffix():
    emit_one, add = get_ops()

    @graph
    def get_two():
        return add(emit_one(), emit_one())

    assert isinstance(get_two, GraphDefinition)

    my_job = get_two.to_job(name="get_two_prod")
    assert my_job.name == "get_two_prod"


def test_partitions():
    @op(config_schema={"date": str})
    def my_op(_):
        pass

    @graph
    def my_graph():
        my_op()

    def config_fn(partition_key: str):
        return {"ops": {"my_op": {"config": {"date": partition_key}}}}

    job_def = my_graph.to_job(
        config=PartitionedConfig(
            run_config_for_partition_key_fn=config_fn,
            partitions_def=StaticPartitionsDefinition(["2020-02-25", "2020-02-26"]),
        ),
    )
    assert job_def.partitions_def
    assert job_def.partitioned_config
    partition_keys = job_def.partitions_def.get_partition_keys()
    assert len(partition_keys) == 2
    assert partition_keys[0] == "2020-02-25"
    assert job_def.partitioned_config.get_run_config_for_partition_key(partition_keys[0]) == {
        "ops": {"my_op": {"config": {"date": "2020-02-25"}}}
    }
    assert job_def.partitioned_config.get_run_config_for_partition_key(partition_keys[1]) == {
        "ops": {"my_op": {"config": {"date": "2020-02-26"}}}
    }

    # Verify that even if the partition set config function mutates shared state
    # when returning run config, the result partitions have different config
    SHARED_CONFIG = {}

    def shared_config_fn(partition_key: str):
        my_config = SHARED_CONFIG
        my_config["ops"] = {"my_op": {"config": {"date": partition_key}}}
        return my_config

    job_def = my_graph.to_job(
        config=PartitionedConfig(
            run_config_for_partition_key_fn=shared_config_fn,
            partitions_def=StaticPartitionsDefinition(["2020-02-25", "2020-02-26"]),
        ),
    )
    assert job_def.partitions_def
    assert job_def.partitioned_config
    partition_keys = job_def.partitions_def.get_partition_keys()
    assert len(partition_keys) == 2
    assert partition_keys[0] == "2020-02-25"

    first_config = job_def.partitioned_config.get_run_config_for_partition_key(partition_keys[0])
    second_config = job_def.partitioned_config.get_run_config_for_partition_key(partition_keys[1])
    assert first_config != second_config

    assert first_config == {"ops": {"my_op": {"config": {"date": "2020-02-25"}}}}
    assert second_config == {"ops": {"my_op": {"config": {"date": "2020-02-26"}}}}


def test_tags_on_job():
    @op
    def basic():
        pass

    @graph
    def basic_graph():
        basic()

    tags = {"my_tag": "yes"}
    job = basic_graph.to_job(tags=tags)
    assert job.tags == tags

    result = job.execute_in_process()
    assert result.success


def test_non_string_tag():
    @op
    def basic():
        pass

    @graph
    def basic_graph():
        basic()

    inner = {"a": "b"}
    tags = {"my_tag": inner}
    job = basic_graph.to_job(tags=tags)
    assert job.tags == {"my_tag": json.dumps(inner)}

    with pytest.raises(DagsterInvalidDefinitionError, match="Invalid value for tag"):
        basic_graph.to_job(tags={"my_tag": basic_graph})


def test_logger_defs():
    @op
    def my_op(_):
        pass

    @graph
    def my_graph():
        my_op()

    @logger  # pyright: ignore[reportCallIssue,reportArgumentType]
    def my_logger(_):
        pass

    my_job = my_graph.to_job(logger_defs={"abc": my_logger})  # pyright: ignore[reportArgumentType]
    assert my_job.loggers == {"abc": my_logger}


def test_job_with_hooks():
    entered = []

    @success_hook
    def basic_hook(_):
        entered.append("yes")

    @op
    def basic_emit():
        pass

    @graph
    def basic_hook_graph():
        basic_emit()

    job_for_hook_testing = basic_hook_graph.to_job(hooks={basic_hook})

    result = job_for_hook_testing.execute_in_process()

    assert result.success
    assert entered == ["yes"]


def test_composition_bug():
    @op
    def expensive_task1():
        pass

    @op
    def expensive_task2(_my_input):
        pass

    @op
    def expensive_task3(_my_input):
        pass

    @graph
    def my_graph1():
        task1_done = expensive_task1()
        _task2_done = expensive_task2(task1_done)

    @graph
    def my_graph2():
        _task3_done = expensive_task3()

    @graph
    def my_graph_final():
        my_graph1()
        my_graph2()

    my_job = my_graph_final.to_job()

    index = my_job.get_job_index()
    assert index.get_node_def_snap("my_graph1")
    assert index.get_node_def_snap("my_graph2")


def test_conflict():
    @op(name="conflict")
    def test_1():
        pass

    @graph(name="conflict")
    def test_2():
        pass

    with pytest.raises(DagsterInvalidDefinitionError, match="definitions with the same name"):

        @graph
        def _conflict_zone():
            test_1()
            test_2()


def test_desc():
    @graph(description="graph desc")
    def empty():
        pass

    job = empty.to_job()
    assert job.description == "graph desc"

    desc = "job desc"
    job = empty.to_job(description=desc)
    assert job.description == desc


def test_config_naming_collisions():
    @op(config_schema={"ops": Permissive()})
    def my_op(context):
        return context.op_config

    @graph
    def my_graph():
        return my_op()

    config = {
        "ops": {"ops": {"foo": {"config": {"foobar": "bar"}}}},
    }
    result = my_graph.execute_in_process(run_config={"ops": {"my_op": {"config": config}}})
    assert result.success
    assert result.output_value() == config

    @graph
    def ops():
        return my_op()

    result = ops.execute_in_process(run_config={"ops": {"my_op": {"config": config}}})
    assert result.success
    assert result.output_value() == config


def test_to_job_incomplete_default_config():
    @op(config_schema={"foo": str})
    def my_op(_):
        pass

    @graph
    def my_graph():
        my_op()

    default_config_error = "Error in config when building job 'my_job' "
    invalid_default_error = "Invalid default_value for Field."
    invalid_configs = [
        (
            {},
            default_config_error,
        ),  # Not providing required config nested into the op config schema.
        (
            {
                "ops": {
                    "my_op": {"config": {"foo": "bar"}},
                    "not_my_op": {"config": {"foo": "bar"}},
                }
            },
            invalid_default_error,
        ),  # Providing extraneous config for an op that doesn't exist.
    ]
    # Ensure that errors nested into the config tree are caught
    for invalid_config, error_msg in invalid_configs:
        with pytest.raises(
            DagsterInvalidConfigError,
            match=error_msg,
        ):
            my_graph.to_job(name="my_job", config=invalid_config)


class TestEnum(enum.Enum):
    ONE = 1
    TWO = 2


def test_enum_config_mapping():
    @op(
        config_schema={
            "my_enum": Field(
                Enum.from_python_enum(TestEnum), is_required=False, default_value="ONE"
            )
        }
    )
    def my_op(context):
        return context.op_config["my_enum"]

    @graph
    def my_graph():
        my_op()

    def _use_defaults_mapping(_):
        return {}

    use_defaults = my_graph.to_job(config=ConfigMapping(config_fn=_use_defaults_mapping))
    result = use_defaults.execute_in_process()
    assert result.success
    assert result.output_for_node("my_op") == TestEnum.ONE

    def _override_defaults_mapping(_):
        return {"ops": {"my_op": {"config": {"my_enum": "TWO"}}}}

    override_defaults = my_graph.to_job(config=ConfigMapping(config_fn=_override_defaults_mapping))
    result = override_defaults.execute_in_process()
    assert result.success
    assert result.output_for_node("my_op") == TestEnum.TWO

    def _ingest_config_mapping(x):
        return {"ops": {"my_op": {"config": {"my_enum": x["my_field"]}}}}

    default_config_mapping = ConfigMapping(
        config_fn=_ingest_config_mapping,
        config_schema=Shape(
            {
                "my_field": Field(
                    Enum.from_python_enum(TestEnum),
                    is_required=False,
                    default_value="TWO",
                )
            }
        ),
        receive_processed_config_values=False,
    )
    ingest_mapping = my_graph.to_job(config=default_config_mapping)
    result = ingest_mapping.execute_in_process()
    assert result.success
    assert result.output_for_node("my_op") == TestEnum.TWO

    no_default_config_mapping = ConfigMapping(
        config_fn=_ingest_config_mapping,
        config_schema=Shape({"my_field": Field(Enum.from_python_enum(TestEnum), is_required=True)}),
        receive_processed_config_values=False,
    )
    ingest_mapping_no_default = my_graph.to_job(config=no_default_config_mapping)
    result = ingest_mapping_no_default.execute_in_process(run_config={"my_field": "TWO"})
    assert result.success
    assert result.output_for_node("my_op") == TestEnum.TWO

    def _ingest_post_processed_config(x):
        assert x["my_field"] == TestEnum.TWO
        return {"ops": {"my_op": {"config": {"my_enum": "TWO"}}}}

    config_mapping_with_preprocessing = ConfigMapping(
        config_fn=_ingest_post_processed_config,
        config_schema=Shape({"my_field": Field(Enum.from_python_enum(TestEnum), is_required=True)}),
    )
    ingest_preprocessing = my_graph.to_job(config=config_mapping_with_preprocessing)
    result = ingest_preprocessing.execute_in_process(run_config={"my_field": "TWO"})
    assert result.success
    assert result.output_for_node("my_op") == TestEnum.TWO


def test_enum_default_config():
    @op(
        config_schema={
            "my_enum": Field(
                Enum.from_python_enum(TestEnum), is_required=False, default_value="ONE"
            )
        }
    )
    def my_op(context):
        return context.op_config["my_enum"]

    @graph
    def my_graph():
        my_op()

    my_job = my_graph.to_job(config={"ops": {"my_op": {"config": {"my_enum": "TWO"}}}})
    result = my_job.execute_in_process()
    assert result.success
    assert result.output_for_node("my_op") == TestEnum.TWO


def test_enum_to_execution():
    @op(
        config_schema={
            "my_enum": Field(
                Enum.from_python_enum(TestEnum), is_required=False, default_value="ONE"
            )
        }
    )
    def my_op(context):
        return context.op_config["my_enum"]

    @graph
    def my_graph():
        my_op()

    my_job = my_graph.to_job()
    result = my_job.execute_in_process()
    assert result.success
    assert result.output_for_node("my_op") == TestEnum.ONE

    result = my_graph.execute_in_process(
        run_config={"ops": {"my_op": {"config": {"my_enum": "TWO"}}}}
    )
    assert result.success
    assert result.output_for_node("my_op") == TestEnum.TWO


def test_raise_on_error_execute_in_process():
    error_str = "My error"

    @op
    def emit_error():
        raise Exception(error_str)

    @graph
    def error_graph():
        emit_error()

    error_job = error_graph.to_job()

    with pytest.raises(Exception, match=error_str):
        error_job.execute_in_process()

    result = error_job.execute_in_process(raise_on_error=False)
    assert not result.success


def test_job_subset():
    @op
    def my_op():
        pass

    @graph
    def basic():
        my_op()
        my_op()

    the_job = basic.to_job()

    assert isinstance(the_job.get_subset(op_selection=["my_op"]), JobDefinition)


def test_tags():
    @graph(tags={"a": "x"})
    def mygraphic():
        pass

    mygraphic_job = mygraphic.to_job()
    assert mygraphic_job.tags == {"a": "x"}
    with DagsterInstance.ephemeral() as instance:
        result = mygraphic_job.execute_in_process(instance=instance)
        assert result.success
        run = instance.get_runs()[0]
        assert run.tags.get("a") == "x"


def test_job_and_graph_tags():
    @graph(tags={"a": "x", "c": "q"})
    def mygraphic():
        pass

    job = mygraphic.to_job(tags={"a": "y", "b": "z"})
    assert job.tags == {"a": "y", "b": "z", "c": "q"}

    with DagsterInstance.ephemeral() as instance:
        result = job.execute_in_process(instance=instance)
        assert result.success
        run = instance.get_runs()[0]
        assert run.tags == {"a": "y", "b": "z", "c": "q"}


def test_output_for_node_non_standard_name():
    @op(out={"foo": Out()})
    def my_op():
        return 5

    @graph
    def basic():
        my_op()

    result = basic.execute_in_process()

    assert result.output_for_node("my_op", "foo") == 5


def test_execute_in_process_aliased_graph():
    @op
    def my_op():
        return 5

    @graph
    def my_graph():
        return my_op()

    result = my_graph.alias("foo_graph").execute_in_process()
    assert result.success
    assert result.output_value() == 5


def test_execute_in_process_aliased_graph_config():
    @op(config_schema=str)
    def my_op(context):
        return context.op_config

    @graph
    def my_graph():
        return my_op()

    result = my_graph.alias("foo_graph").execute_in_process(
        run_config={"ops": {"my_op": {"config": "foo"}}}
    )
    assert result.success
    assert result.output_value() == "foo"


def test_job_name_valid():
    with pytest.raises(DagsterInvalidDefinitionError):

        @graph
        def my_graph():
            pass

        my_graph.to_job(name="a/b")


def test_top_level_config_mapping_graph():
    @op(config_schema=str)
    def my_op(context):
        return context.op_config

    def _config_fn(_):
        return {"my_op": {"config": "foo"}}

    @graph(config=ConfigMapping(config_fn=_config_fn))
    def my_graph():
        my_op()

    result = my_graph.execute_in_process()

    assert result.success
    assert result.output_for_node("my_op") == "foo"


def test_top_level_config_mapping_config_schema():
    @op(config_schema=str)
    def my_op(context):
        return context.op_config

    def _config_fn(outer):
        return {"my_op": {"config": outer}}

    @graph(config=ConfigMapping(config_fn=_config_fn, config_schema=str))
    def my_graph():
        my_op()

    result = my_graph.to_job().execute_in_process(run_config={"ops": {"config": "foo"}})

    assert result.success
    assert result.output_for_node("my_op") == "foo"

    my_job = my_graph.to_job(config={"ops": {"config": "foo"}})
    result = my_job.execute_in_process()
    assert result.success
    assert result.output_for_node("my_op") == "foo"


def test_nested_graph_config_mapping():
    @op(config_schema=str)
    def my_op(context):
        return context.op_config

    def _nested_config_fn(outer):
        return {"my_op": {"config": outer}}

    @graph(config=ConfigMapping(config_fn=_nested_config_fn, config_schema=str))
    def my_nested_graph():
        my_op()

    def _config_fn(outer):
        return {"my_nested_graph": {"config": outer}}

    @graph(config=ConfigMapping(config_fn=_config_fn, config_schema=str))
    def my_graph():
        my_nested_graph()

    result = my_graph.to_job().execute_in_process(run_config={"ops": {"config": "foo"}})

    assert result.success
    assert result.output_for_node("my_nested_graph.my_op") == "foo"


def test_top_level_graph_config_mapping_failure():
    @op(config_schema=str)
    def my_op(context):
        return context.op_config

    def _nested_config_fn(_):
        return "foo"

    @graph(config=ConfigMapping(config_fn=_nested_config_fn))
    def my_nested_graph():
        my_op()

    with pytest.raises(
        DagsterInvalidConfigError,
        match=(
            "In job 'my_nested_graph', top level graph 'my_nested_graph' has a configuration error."
        ),
    ):
        my_nested_graph.execute_in_process()


def test_top_level_graph_outer_config_failure():
    @op(config_schema=str)
    def my_op(context):
        return context.op_config

    def _config_fn(outer):
        return {"my_op": {"config": outer}}

    @graph(config=ConfigMapping(config_fn=_config_fn, config_schema=str))
    def my_graph():
        my_op()

    with pytest.raises(DagsterInvalidConfigError, match="Invalid scalar at path root:ops:config"):
        my_graph.to_job().execute_in_process(run_config={"ops": {"config": {"bad_type": "foo"}}})

    with pytest.raises(DagsterInvalidConfigError, match="Invalid scalar at path root:config"):
        my_graph.to_job(config={"ops": {"config": {"bad_type": "foo"}}})


def test_graph_dict_config():
    @op(config_schema=str)
    def my_op(context):
        return context.op_config

    @graph(config={"my_op": {"config": "foo"}})
    def my_graph():
        return my_op()

    result = my_graph.execute_in_process()
    assert result.success

    assert result.output_value() == "foo"


def test_graph_with_configured():
    @op(config_schema=str)
    def my_op(context):
        return context.op_config

    def _config_fn(outer):
        return {"my_op": {"config": outer}}

    @graph(config=ConfigMapping(config_fn=_config_fn, config_schema=str))
    def my_graph():
        my_op()

    result = my_graph.configured(name="my_graph", config_or_config_fn="foo").execute_in_process()
    assert result.success
    assert result.output_for_node("my_op") == "foo"

    def _configured_use_fn(outer):
        return outer

    result = (
        my_graph.configured(
            name="my_graph", config_or_config_fn=_configured_use_fn, config_schema=str
        )
        .to_job()
        .execute_in_process(run_config={"ops": {"config": "foo"}})
    )

    assert result.success
    assert result.output_for_node("my_op") == "foo"


def test_graph_configured_error_in_config():
    @op(config_schema=str)
    def my_op(context):
        return context.op_config

    def _config_fn(outer):
        return {"my_op": {"config": outer}}

    @graph(config=ConfigMapping(config_fn=_config_fn, config_schema=str))
    def my_graph():
        my_op()

    def _bad_config_fn(_):
        return 2

    configured_graph = my_graph.configured(name="blah", config_or_config_fn=_bad_config_fn)

    with pytest.raises(DagsterInvalidConfigError, match="Error in config for graph blah"):
        configured_graph.execute_in_process()


def test_graph_configured_error_in_fn():
    @op(config_schema=str)
    def my_op(context):
        return context.op_config

    def _config_fn(outer):
        return {"my_op": {"config": outer}}

    @graph(config=ConfigMapping(config_fn=_config_fn, config_schema=str))
    def my_graph():
        my_op()

    def _bad_config_fn(_):
        raise Exception("Uh oh")

    configured_graph = my_graph.configured(name="blah", config_or_config_fn=_bad_config_fn)

    with pytest.raises(
        DagsterConfigMappingFunctionError,
        match=(
            "The config mapping function on a `configured` GraphDefinition has thrown an "
            "unexpected error during its execution."
        ),
    ):
        configured_graph.execute_in_process()


def test_job_non_default_logger_config():
    @graph
    def your_graph():
        pass

    your_job = your_graph.to_job(
        logger_defs={"json": json_console_logger},
        config={"loggers": {"json": {"config": {}}}},
    )

    result = your_job.execute_in_process()
    assert result.success
    result = your_job.execute_in_process(
        run_config={"loggers": {"json": {"config": {"log_level": "DEBUG"}}}}
    )
    assert result.success


def test_job_partitions_def():
    @op
    def my_op(context):
        assert context.has_partition_key
        assert context.partition_key == "2020-01-01"
        assert context.partition_time_window == TimeWindow(
            parse_time_string("2020-01-01"), parse_time_string("2020-01-02")
        )

    @graph
    def my_graph():
        my_op()

    my_job = my_graph.to_job(partitions_def=DailyPartitionsDefinition(start_date="2020-01-01"))
    assert my_job.execute_in_process(partition_key="2020-01-01").success


def test_graph_top_level_input():
    @op
    def my_op(x, y):
        return x + y

    @graph
    def my_graph(x, y):
        return my_op(x, y)

    result = my_graph.execute_in_process(
        run_config={"inputs": {"x": {"value": 2}, "y": {"value": 3}}}
    )
    assert result.success
    assert result.output_for_node("my_op") == 5

    @graph
    def my_graph_with_nesting(x):
        my_graph(x, x)

    result = my_graph_with_nesting.execute_in_process(run_config={"inputs": {"x": {"value": 2}}})
    assert result.success
    assert result.output_for_node("my_graph.my_op") == 4


def test_run_id_execute_in_process():
    @graph
    def blank():
        pass

    with instance_for_test() as instance:
        result_one = blank.execute_in_process(instance=instance)
        assert result_one.success
        assert instance.get_run_by_id(result_one.dagster_run.run_id)

        result_two = blank.to_job().execute_in_process(instance=instance)
        assert result_two.success
        assert instance.get_run_by_id(result_two.dagster_run.run_id)
        assert result_one.dagster_run.run_id != result_two.dagster_run.run_id

        result_three = blank.alias("some_name").execute_in_process(instance=instance)
        assert result_three.success
        assert instance.get_run_by_id(result_three.dagster_run.run_id)
        assert result_three.dagster_run.run_id not in set(
            [result_one.dagster_run.run_id, result_two.dagster_run.run_id]
        )


def test_graphs_break_type_checks():
    # Test to ensure we use grab the type from correct input def along mapping chains for type checks.

    @op
    def emit_str():
        return "one"

    @op
    def echo_int(y: int):
        assert isinstance(y, int), "type checks should fail before op invocation"
        return y

    @graph
    def no_repro():
        echo_int(emit_str())

    with pytest.raises(DagsterTypeCheckDidNotPass):
        no_repro.execute_in_process()

    @graph
    def map_any(x):
        echo_int(x)

    @graph
    def repro():
        map_any(emit_str())

    with pytest.raises(DagsterTypeCheckDidNotPass):
        repro.execute_in_process()

    @graph
    def map_str(x: str):
        echo_int(x)

    @graph
    def repro_2():
        map_str(emit_str())

    with pytest.raises(DagsterTypeCheckDidNotPass):
        repro_2.execute_in_process()


def test_to_job_input_values():
    @op
    def my_op(x, y):
        return x + y

    @graph
    def my_graph(x, y):
        return my_op(x, y)

    result = my_graph.to_job(input_values={"x": 5, "y": 6}).execute_in_process()
    assert result.success
    assert result.output_value() == 11

    result = my_graph.alias("blah").to_job(input_values={"x": 5, "y": 6}).execute_in_process()
    assert result.success
    assert result.output_value() == 11

    # Test partial input value specification
    result = my_graph.to_job(input_values={"x": 5}).execute_in_process(input_values={"y": 6})
    assert result.success
    assert result.output_value() == 11

    # Test input value specification override
    result = my_graph.to_job(input_values={"x": 5, "y": 6}).execute_in_process(
        input_values={"y": 7}
    )
    assert result.success
    assert result.output_value() == 12


def test_input_values_name_not_found():
    @op
    def my_op(x, y):
        return x + y

    @graph
    def my_graph(x, y):
        return my_op(x, y)

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "Error when constructing JobDefinition 'my_graph': Input value provided for key 'z',"
            " but job has no top-level input with that name."
        ),
    ):
        my_graph.to_job(input_values={"z": 4})


def test_input_values_override_default():
    @op(ins={"x": In(default_value=5)})
    def op_with_default_input(x):
        return x

    @graph
    def my_graph(x):
        return op_with_default_input(x)

    result = my_graph.execute_in_process(input_values={"x": 6})
    assert result.success
    assert result.output_value() == 6


def test_unsatisfied_input_nested():
    @op
    def ingest(x: datetime) -> str:
        return str(x)

    @graph
    def the_graph(x):
        ingest(x)

    @graph
    def the_top_level_graph():
        the_graph()

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Input 'x' of graph 'the_graph' has no way of being resolved.",
    ):
        the_top_level_graph.to_job()


def test_all_dagster_types():
    class Foo:
        pass

    class Bar(Foo):
        pass

    @op
    def my_op(x: Foo):
        return x

    @op
    def my_op_2(x: Foo):
        return x

    @graph
    def my_graph(x: Optional[Bar]):
        y = x or Foo()
        my_op_2(my_op(y))

    names = [x.display_name for x in my_graph.all_dagster_types()]

    assert "Foo" in names
    assert "Bar" in names
    assert "Bar?" in names


def test_graph_definition_input_mappings():
    @op
    def inner_op(int_input: int) -> int:
        return int_input + 7

    the_graph = GraphDefinition(
        name="the_graph",
        input_mappings=[
            InputMapping(
                graph_input_name="x",
                mapped_node_name="inner_op",
                mapped_node_input_name="int_input",
                graph_input_description="hello",
            )
        ],
        node_defs=[inner_op],
    )
    assert the_graph.execute_in_process(input_values={"x": 5}).output_for_node("inner_op") == 12

    @op
    def outer_op() -> int:
        return 5

    @graph
    def link():
        the_graph(outer_op())

    assert link.execute_in_process().output_for_node("the_graph.inner_op") == 12


def test_graph_with_mapped_out():
    @op(out=DynamicOut())
    def dyn_vals():
        for i in range(3):
            yield DynamicOutput(i, mapping_key=f"num_{i}")

    @op
    def echo(x):
        return x

    @op
    def double(x):
        return x * 2

    @op
    def total(nums):
        return sum(nums)

    @graph
    def mapped_out():
        return dyn_vals().map(echo)

    result = mapped_out.execute_in_process()
    assert result.success
    assert result.output_value() == {"num_0": 0, "num_1": 1, "num_2": 2}


def test_infer_graph_input_type_from_inner_input():
    @op(ins={"in1": In(Nothing)})
    def op1(): ...

    @graph
    def graph1(in1):
        op1(in1)

    assert graph1.input_defs[0].dagster_type.is_nothing

    assert graph1.execute_in_process().success


def test_infer_graph_input_type_from_inner_input_int():
    @op
    def op1(in1: int):
        assert in1 == 5

    @graph
    def graph1(in1):
        op1(in1)

    assert graph1.input_defs[0].dagster_type.typing_type == int

    assert graph1.execute_in_process(run_config={"inputs": {"in1": {"value": 5}}}).success


def test_infer_graph_input_type_from_inner_input_explicit_any():
    @op(ins={"in1": In(Nothing)})
    def op1(): ...

    @graph
    def graph1(in1: Any):
        op1(in1)

    assert graph1.input_defs[0].dagster_type.is_nothing

    assert graph1.execute_in_process().success


def test_infer_graph_input_type_from_inner_input_explicit_graphin_type():
    @op(ins={"in1": In(Nothing)})
    def op1(): ...

    @graph
    def graph1(in1: int):
        op1(in1)

    assert graph1.input_defs[0].dagster_type.typing_type == int


def test_infer_graph_input_type_from_multiple_inner_inputs():
    @op(ins={"in1": In(Nothing)})
    def op1(): ...

    @op(ins={"in2": In(Nothing)})
    def op2(): ...

    @graph
    def graph1(in1):
        op1(in1)
        op2(in1)

    assert graph1.input_defs[0].dagster_type.is_nothing

    assert graph1.execute_in_process().success


def test_dont_infer_graph_input_type_from_different_inner_inputs():
    @op(ins={"in1": In(Nothing)})
    def op1(): ...

    @op
    def op2(in2):
        del in2

    @graph
    def graph1(in1):
        op1(in1)
        op2(in1)

    assert not graph1.input_defs[0].dagster_type.is_nothing

    with pytest.raises(DagsterInvalidConfigError):
        graph1.execute_in_process()


def test_infer_graph_input_type_from_inner_inner_input():
    @op(ins={"in1": In(Nothing)})
    def op1(): ...

    @graph
    def inner(in1):
        op1(in1)

    @graph
    def outer(in1):
        inner(in1)

    assert outer.input_defs[0].dagster_type.is_nothing

    assert outer.execute_in_process().success


def test_infer_graph_input_type_from_inner_input_fan_in():
    @op
    def op1(in1: list[int]):
        assert in1 == [5]

    @graph
    def graph1(in1):
        op1([in1])

    assert graph1.input_defs[0].dagster_type.typing_type == int

    assert graph1.execute_in_process(run_config={"inputs": {"in1": {"value": 5}}}).success


def test_infer_graph_input_type_from_inner_input_mixed_fan_in():
    @op
    def op1(in1: list[int], in2: int):
        assert in1 == [5]
        assert in2 == 5

    @graph
    def graph1(in1):
        op1([in1], in1)

    assert graph1.input_defs[0].dagster_type.typing_type == int

    assert graph1.execute_in_process(run_config={"inputs": {"in1": {"value": 5}}}).success


def test_input_manager_key_and_custom_dagster_type_resolved():
    class CustomType:
        def __init__(self, value):
            self.value = value

    @input_manager
    def data_input_manager():
        return CustomType(5)

    @op(ins={"df_train": In(CustomType, input_manager_key="data_input_manager")})
    def target_extractor_op(df_train):
        return 1

    @graph(
        out={"target": GraphOut()},
    )
    def target_extractor_graph():
        target = target_extractor_op()
        return target

    local_target_extractor_job = target_extractor_graph.to_job(
        name="target_extractor_job",
        resource_defs={"data_input_manager": data_input_manager},
    )
    assert local_target_extractor_job.execute_in_process().success


def test_collision():
    numbers = count()

    @op
    def next_num():
        return next(numbers)

    @op
    def echo(context, value):
        return value

    @graph
    def composed(value):
        echo(value)
        return next_num()

    @graph
    def collision_test():
        starting_value = next_num()
        composed(starting_value)
        composed(starting_value)

    result = collision_test.execute_in_process()
    assert result.output_for_node("composed.echo") == 0
    assert result.output_for_node("composed_2.echo") == 0
