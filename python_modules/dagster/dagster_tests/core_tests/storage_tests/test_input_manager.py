import tempfile

import pytest
from dagster import (
    DagsterInstance,
    DagsterInvalidDefinitionError,
    EventMetadataEntry,
    IOManager,
    InputDefinition,
    ModeDefinition,
    OutputDefinition,
    PythonObjectDagsterType,
    RootInputManagerDefinition,
    execute_pipeline,
    fs_io_manager,
    io_manager,
    pipeline,
    resource,
    root_input_manager,
    solid,
)
from dagster.core.definitions.events import Failure, RetryRequested
from dagster.core.instance import InstanceRef


def test_validate_inputs():
    @root_input_manager
    def my_loader(_):
        return 5

    @solid(
        input_defs=[
            InputDefinition(
                "input1", dagster_type=PythonObjectDagsterType(int), root_manager_key="my_loader"
            )
        ]
    )
    def my_solid(_, input1):
        return input1

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"my_loader": my_loader})])
    def my_pipeline():
        my_solid()

    execute_pipeline(my_pipeline)


def test_root_input_manager():
    @root_input_manager
    def my_hardcoded_csv_loader(_context):
        return 5

    @solid(input_defs=[InputDefinition("input1", root_manager_key="my_loader")])
    def solid1(_, input1):
        assert input1 == 5

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"my_loader": my_hardcoded_csv_loader})])
    def my_pipeline():
        solid1()

    execute_pipeline(my_pipeline)


def test_configurable_root_input_manager():
    @root_input_manager(config_schema={"base_dir": str}, input_config_schema={"value": int})
    def my_configurable_csv_loader(context):
        assert context.resource_config["base_dir"] == "abc"
        return context.config["value"]

    @solid(input_defs=[InputDefinition("input1", root_manager_key="my_loader")])
    def solid1(_, input1):
        assert input1 == 5

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"my_loader": my_configurable_csv_loader})])
    def my_configurable_pipeline():
        solid1()

    execute_pipeline(
        my_configurable_pipeline,
        run_config={
            "solids": {"solid1": {"inputs": {"input1": {"value": 5}}}},
            "resources": {"my_loader": {"config": {"base_dir": "abc"}}},
        },
    )


def test_only_used_for_root():
    metadata = {"name": 5}

    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            output = context.upstream_output
            assert output.metadata == metadata
            assert output.name == "my_output"
            assert output.step_key == "solid1"
            assert context.pipeline_name == "my_pipeline"
            assert context.solid_def.name == solid2.name
            return 5

    @io_manager
    def my_io_manager(_):
        return MyIOManager()

    @solid(
        output_defs=[
            OutputDefinition(name="my_output", io_manager_key="my_io_manager", metadata=metadata)
        ]
    )
    def solid1(_):
        return 1

    @solid(input_defs=[InputDefinition("input1", root_manager_key="my_root_manager")])
    def solid2(_, input1):
        assert input1 == 5

    @root_input_manager
    def root_manager(_):
        assert False, "should not be called"

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "my_io_manager": my_io_manager,
                    "my_root_manager": root_manager,
                }
            )
        ]
    )
    def my_pipeline():
        solid2(solid1())

    execute_pipeline(my_pipeline)


def test_configured():
    @root_input_manager(
        config_schema={"base_dir": str},
        description="abc",
        input_config_schema={"format": str},
        required_resource_keys={"r1", "r2"},
        version="123",
    )
    def my_input_manager(_):
        pass

    configured_input_manager = my_input_manager.configured({"base_dir": "/a/b/c"})

    assert isinstance(configured_input_manager, RootInputManagerDefinition)
    assert configured_input_manager.description == my_input_manager.description
    assert (
        configured_input_manager.required_resource_keys == my_input_manager.required_resource_keys
    )
    assert configured_input_manager.version is None


def test_input_manager_with_failure():
    @root_input_manager
    def should_fail(_):
        raise Failure(
            description="Foolure",
            metadata_entries=[
                EventMetadataEntry.text(label="label", text="text", description="description")
            ],
        )

    @solid(input_defs=[InputDefinition("_fail_input", root_manager_key="should_fail")])
    def fail_on_input(_, _fail_input):
        assert False, "should not be called"

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"should_fail": should_fail})])
    def simple():
        fail_on_input()

    with tempfile.TemporaryDirectory() as tmpdir_path:

        instance = DagsterInstance.from_ref(InstanceRef.from_dir(tmpdir_path))

        result = execute_pipeline(simple, instance=instance, raise_on_error=False)

        assert not result.success

        failure_data = result.result_for_solid("fail_on_input").failure_data

        assert failure_data.error.cls_name == "Failure"

        assert failure_data.user_failure_data.description == "Foolure"
        assert failure_data.user_failure_data.metadata_entries[0].label == "label"
        assert failure_data.user_failure_data.metadata_entries[0].entry_data.text == "text"
        assert failure_data.user_failure_data.metadata_entries[0].description == "description"


def test_input_manager_with_retries():
    _count = {"total": 0}

    @root_input_manager
    def should_succeed_after_retries(_):
        if _count["total"] < 2:
            _count["total"] += 1
            raise RetryRequested(max_retries=3)
        return "foo"

    @root_input_manager
    def should_retry(_):
        raise RetryRequested(max_retries=3)

    @solid(
        input_defs=[InputDefinition("solid_input", root_manager_key="should_succeed_after_retries")]
    )
    def take_input_1(_, solid_input):
        return solid_input

    @solid(input_defs=[InputDefinition("solid_input", root_manager_key="should_retry")])
    def take_input_2(_, solid_input):
        return solid_input

    @solid
    def take_input_3(_, _input1, _input2):
        assert False, "should not be called"

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "should_succeed_after_retries": should_succeed_after_retries,
                    "should_retry": should_retry,
                }
            )
        ]
    )
    def simple():
        take_input_3(take_input_2(), take_input_1())

    with tempfile.TemporaryDirectory() as tmpdir_path:

        instance = DagsterInstance.from_ref(InstanceRef.from_dir(tmpdir_path))

        result = execute_pipeline(simple, instance=instance, raise_on_error=False)

        step_stats = instance.get_run_step_stats(result.run_id)
        assert len(step_stats) == 2

        step_stats_1 = instance.get_run_step_stats(result.run_id, step_keys=["take_input_1"])
        assert len(step_stats_1) == 1
        step_stat_1 = step_stats_1[0]
        assert step_stat_1.status.value == "SUCCESS"
        assert step_stat_1.attempts == 3

        step_stats_2 = instance.get_run_step_stats(result.run_id, step_keys=["take_input_2"])
        assert len(step_stats_2) == 1
        step_stat_2 = step_stats_2[0]
        assert step_stat_2.status.value == "FAILURE"
        assert step_stat_2.attempts == 4

        step_stats_3 = instance.get_run_step_stats(result.run_id, step_keys=["take_input_3"])
        assert len(step_stats_3) == 0


def test_input_manager_resource_config():
    @root_input_manager(config_schema={"dog": str})
    def emit_dog(context):
        assert context.resource_config["dog"] == "poodle"

    @solid(input_defs=[InputDefinition("solid_input", root_manager_key="emit_dog")])
    def source_solid(_, solid_input):
        return solid_input

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"emit_dog": emit_dog})])
    def basic_pipeline():
        return source_solid(source_solid())

    result = execute_pipeline(
        basic_pipeline, run_config={"resources": {"emit_dog": {"config": {"dog": "poodle"}}}}
    )

    assert result.success


def test_input_manager_required_resource_keys():
    @resource
    def foo_resource(_):
        return "foo"

    @root_input_manager(required_resource_keys={"foo_resource"})
    def root_input_manager_reqs_resources(context):
        assert context.resources.foo_resource == "foo"

    @solid(
        input_defs=[
            InputDefinition("_manager_input", root_manager_key="root_input_manager_reqs_resources")
        ]
    )
    def big_solid(_, _manager_input):
        return "manager_input"

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "root_input_manager_reqs_resources": root_input_manager_reqs_resources,
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
    @solid(input_defs=[InputDefinition("_input", root_manager_key="not_here")])
    def solid_requires_manager(_, _input):
        pass

    @pipeline
    def basic():
        solid_requires_manager()

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match='Input "_input" for solid "solid_requires_manager" requires root_manager_key "not_here", but no '
        "resource has been provided. Please include a resource definition for that key in the "
        "resource_defs of your ModeDefinition.",
    ):
        execute_pipeline(basic)


def test_resource_not_input_manager():
    @resource
    def resource_not_manager(_):
        return "foo"

    @solid(input_defs=[InputDefinition("_input", root_manager_key="not_manager")])
    def solid_requires_manager(_, _input):
        pass

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"not_manager": resource_not_manager})])
    def basic():
        solid_requires_manager()

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match='Input "_input" for solid "solid_requires_manager" requires root_manager_key '
        '"not_manager", but the resource definition provided is not an '
        "IInputManagerDefinition",
    ):
        execute_pipeline(basic)
