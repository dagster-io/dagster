import tempfile

import pytest
from dagster import (
    AssetMaterialization,
    DagsterInstance,
    DagsterInvalidDefinitionError,
    DagsterType,
    EventMetadataEntry,
    Failure,
    IOManager,
    InputDefinition,
    ModeDefinition,
    Output,
    OutputDefinition,
    RetryRequested,
    dagster_type_materializer,
    execute_pipeline,
    io_manager,
    pipeline,
    resource,
    solid,
)
from dagster.core.instance import InstanceRef
from dagster.core.storage.output_manager import OutputManagerDefinition, output_manager


def test_output_manager():
    adict = {}

    @output_manager
    def my_output_manager(_context, obj):
        adict["result"] = obj

    @solid(output_defs=[OutputDefinition(io_manager_key="my_output_manager")])
    def my_solid(_):
        return 5

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"my_output_manager": my_output_manager})])
    def my_pipeline():
        my_solid()

    execute_pipeline(my_pipeline)

    assert adict["result"] == 5


def test_configurable_output_manager():
    adict = {}

    @output_manager(output_config_schema=str)
    def my_output_manager(context, obj):
        adict["result"] = (context.config, obj)

    @solid(output_defs=[OutputDefinition(name="my_output", io_manager_key="my_output_manager")])
    def my_solid(_):
        return 5

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"my_output_manager": my_output_manager})])
    def my_pipeline():
        my_solid()

    execute_pipeline(
        my_pipeline, run_config={"solids": {"my_solid": {"outputs": {"my_output": "a"}}}}
    )

    assert adict["result"] == ("a", 5)


def test_type_materializer_and_configurable_output_manager():
    @dagster_type_materializer(config_schema={"type_materializer_path": str})
    def my_materializer(_, _config, _value):
        assert False, "shouldn't get here"

    adict = {}

    @output_manager(output_config_schema={"output_manager_path": str})
    def my_output_manager(_context, obj):
        adict["result"] = obj

    my_type = DagsterType(lambda _, _val: True, name="my_type", materializer=my_materializer)

    @solid(
        output_defs=[
            OutputDefinition(
                name="output1", io_manager_key="my_output_manager", dagster_type=my_type
            ),
            OutputDefinition(name="output2", dagster_type=my_type),
        ]
    )
    def my_solid(_):
        yield Output(5, "output1")
        yield Output(7, "output2")

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"my_output_manager": my_output_manager})])
    def my_pipeline():
        my_solid()

    execute_pipeline(
        my_pipeline,
        run_config={"solids": {"my_solid": {"outputs": {"output1": {"output_manager_path": "a"}}}}},
    )

    assert adict["result"] == 5


def test_type_materializer_and_nonconfigurable_output_manager():
    adict = {}

    @dagster_type_materializer(config_schema={"type_materializer_path": str})
    def my_materializer(_, _config, _value):
        adict["materialized"] = True
        return AssetMaterialization(asset_key="a")

    @output_manager
    def my_output_manager(_context, obj):
        adict["result"] = obj

    my_type = DagsterType(lambda _, _val: True, name="my_type", materializer=my_materializer)

    @solid(
        output_defs=[
            OutputDefinition(
                name="output1", io_manager_key="my_output_manager", dagster_type=my_type
            ),
            OutputDefinition(name="output2", dagster_type=my_type),
        ]
    )
    def my_solid(_):
        yield Output(5, "output1")
        yield Output(7, "output2")

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"my_output_manager": my_output_manager})])
    def my_pipeline():
        my_solid()

    execute_pipeline(
        my_pipeline,
        run_config={
            "solids": {"my_solid": {"outputs": [{"output1": {"type_materializer_path": "a"}}]}}
        },
    )

    assert adict["result"] == 5
    assert adict["materialized"]


def test_configured():
    @output_manager(
        config_schema={"base_dir": str},
        description="abc",
        output_config_schema={"format": str},
        required_resource_keys={"r1", "r2"},
        version="123",
    )
    def my_output_manager(_):
        pass

    configured_output_manager = my_output_manager.configured({"base_dir": "/a/b/c"})

    assert isinstance(configured_output_manager, OutputManagerDefinition)
    assert configured_output_manager.description == my_output_manager.description
    assert configured_output_manager.output_config_schema == my_output_manager.output_config_schema
    assert (
        configured_output_manager.required_resource_keys == my_output_manager.required_resource_keys
    )
    assert configured_output_manager.version is None


def test_output_manager_with_failure():
    _called_input_manager = False
    _called_solid = False

    @output_manager
    def should_fail(_, _obj):
        raise Failure(
            description="Foolure",
            metadata_entries=[
                EventMetadataEntry.text(label="label", text="text", description="description")
            ],
        )

    @solid(output_defs=[OutputDefinition(io_manager_key="should_fail")])
    def emit_str(_):
        return "emit"

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"should_fail": should_fail})])
    def simple():
        emit_str()

    with tempfile.TemporaryDirectory() as tmpdir_path:

        instance = DagsterInstance.from_ref(InstanceRef.from_dir(tmpdir_path))

        result = execute_pipeline(simple, instance=instance, raise_on_error=False)

        assert not result.success

        failure_data = result.result_for_solid("emit_str").failure_data

        assert failure_data.error.cls_name == "Failure"

        assert failure_data.user_failure_data.description == "Foolure"
        assert failure_data.user_failure_data.metadata_entries[0].label == "label"
        assert failure_data.user_failure_data.metadata_entries[0].entry_data.text == "text"
        assert failure_data.user_failure_data.metadata_entries[0].description == "description"

        assert not _called_input_manager and not _called_solid


def test_output_manager_with_retries():
    _called = False
    _count = {"total": 0}

    @io_manager
    def should_succeed(_):
        class FakeIOManager(IOManager):
            def load_input(self, _context):
                return "foo"

            def handle_output(self, _context, _obj):
                if _count["total"] < 2:
                    _count["total"] += 1
                    raise RetryRequested(max_retries=3)

        return FakeIOManager()

    @io_manager
    def should_retry(_):
        class FakeIOManager(IOManager):
            def load_input(self, _context):
                return "foo"

            def handle_output(self, _context, _obj):
                raise RetryRequested(max_retries=3)

        return FakeIOManager()

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={"should_succeed": should_succeed, "should_retry": should_retry,}
            )
        ]
    )
    def simple():
        @solid(output_defs=[OutputDefinition(io_manager_key="should_succeed")],)
        def source_solid(_):
            return "foo"

        @solid(
            input_defs=[InputDefinition("solid_input")],
            output_defs=[OutputDefinition(io_manager_key="should_retry")],
        )
        def take_input(_, solid_input):
            return solid_input

        @solid(input_defs=[InputDefinition("_solid_input")])
        def should_not_execute(_, _solid_input):
            _called = True

        should_not_execute(take_input(source_solid()))

    with tempfile.TemporaryDirectory() as tmpdir_path:

        instance = DagsterInstance.from_ref(InstanceRef.from_dir(tmpdir_path))

        result = execute_pipeline(simple, instance=instance, raise_on_error=False)

        step_stats = instance.get_run_step_stats(result.run_id)
        assert len(step_stats) == 2

        step_stats_1 = instance.get_run_step_stats(result.run_id, step_keys=["source_solid"])
        assert len(step_stats_1) == 1
        step_stat_1 = step_stats_1[0]
        assert step_stat_1.status.value == "SUCCESS"
        assert step_stat_1.attempts == 3

        step_stats_2 = instance.get_run_step_stats(result.run_id, step_keys=["take_input"])
        assert len(step_stats_2) == 1
        step_stat_2 = step_stats_2[0]
        assert step_stat_2.status.value == "FAILURE"
        assert step_stat_2.attempts == 4

        step_stats_3 = instance.get_run_step_stats(result.run_id, step_keys=["should_not_execute"])
        assert len(step_stats_3) == 0
        assert _called == False


def test_output_manager_no_input_manager():
    @output_manager
    def output_manager_alone(_):
        raise NotImplementedError()

    @solid(
        output_defs=[OutputDefinition(name="output_alone", io_manager_key="output_manager_alone")]
    )
    def emit_str(_):
        raise NotImplementedError()

    @solid(input_defs=[InputDefinition("_str_input")])
    def ingest_str(_, _str_input):
        raise NotImplementedError()

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match='Input "_str_input" of solid "ingest_str" is connected to output "output_alone" of '
        'solid "emit_str". In mode "default", that output does not have an output manager that '
        "knows how to load inputs, so we don't know how to load the input. To address this, "
        "assign an IOManager to the upstream output.",
    ):

        @pipeline(
            mode_defs=[
                ModeDefinition(
                    "default", resource_defs={"output_manager_alone": output_manager_alone}
                )
            ]
        )
        def _should_fail():
            ingest_str(emit_str())


def test_output_manager_resource_config():
    @output_manager(config_schema={"is_foo": str})
    def emit_foo(context, _obj):
        assert context.resource_config["is_foo"] == "yes"

    @solid(output_defs=[OutputDefinition(io_manager_key="emit_foo")])
    def basic_solid(_):
        return "foo"

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"emit_foo": emit_foo})])
    def return_foo():
        return basic_solid()

    result = execute_pipeline(
        return_foo, run_config={"resources": {"emit_foo": {"config": {"is_foo": "yes"}}}}
    )

    assert result.success


def test_output_manager_required_resource_keys():
    @resource
    def foo_resource(_):
        return "foo"

    @output_manager(required_resource_keys={"foo_resource"})
    def output_manager_reqs_resources(context, _obj):
        assert context.resources.foo_resource == "foo"

    @solid(
        output_defs=[
            OutputDefinition(dagster_type=str, io_manager_key="output_manager_reqs_resources")
        ]
    )
    def big_solid(_):
        return "output"

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "output_manager_reqs_resources": output_manager_reqs_resources,
                    "foo_resource": foo_resource,
                }
            )
        ]
    )
    def basic_pipeline():
        big_solid()

    result = execute_pipeline(basic_pipeline)

    assert result.success


def test_manager_not_provided():
    @solid(output_defs=[OutputDefinition(io_manager_key="not_here")])
    def solid_requires_manager(_, _input):
        return "foo"

    @pipeline
    def basic():
        solid_requires_manager()

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match='Output "result" for solid "solid_requires_manager" requires io_manager_key "not_here", but no '
        "resource has been provided. Please include a resource definition for that key in the "
        "resource_defs of your ModeDefinition.",
    ):
        execute_pipeline(basic)


def test_resource_not_output_manager():
    @resource
    def resource_not_manager(_):
        return "foo"

    @solid(output_defs=[OutputDefinition(io_manager_key="not_manager")])
    def solid_requires_manager(_):
        return "foo"

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"not_manager": resource_not_manager})])
    def basic():
        solid_requires_manager()

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match='Output "result" for solid "solid_requires_manager" requires io_manager_key '
        '"not_manager", but the resource definition provided is not an '
        "IOutputManagerDefinition",
    ):
        execute_pipeline(basic)
