from dagster import (
    DagsterInstance,
    EventMetadataEntry,
    InputDefinition,
    InputManagerDefinition,
    ModeDefinition,
    ObjectManager,
    OutputDefinition,
    PythonObjectDagsterType,
    execute_pipeline,
    pipeline,
    resource,
    seven,
    solid,
)
from dagster.core.definitions.events import Failure, RetryRequested
from dagster.core.instance import InstanceRef
from dagster.core.storage.input_manager import input_manager


def test_validate_inputs():
    @input_manager
    def my_loader(_, _resource_config):
        return 5

    @solid(
        input_defs=[
            InputDefinition(
                "input1", dagster_type=PythonObjectDagsterType(int), manager_key="my_loader"
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
    @input_manager
    def my_hardcoded_csv_loader(_context, _resource_config):
        return 5

    @solid(input_defs=[InputDefinition("input1", manager_key="my_loader")])
    def solid1(_, input1):
        assert input1 == 5

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"my_loader": my_hardcoded_csv_loader})])
    def my_pipeline():
        solid1()

    execute_pipeline(my_pipeline)


def test_configurable_root_input_manager():
    @input_manager(config_schema={"base_dir": str}, input_config_schema={"value": int})
    def my_configurable_csv_loader(context, resource_config):
        assert resource_config["base_dir"] == "abc"
        return context.config["value"]

    @solid(input_defs=[InputDefinition("input1", manager_key="my_loader")])
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


def test_override_object_manager():
    metadata = {"name": 5}

    class MyObjectManager(ObjectManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            assert False, "should not be called"

    @resource
    def my_object_manager(_):
        return MyObjectManager()

    @solid(
        output_defs=[
            OutputDefinition(name="my_output", manager_key="my_object_manager", metadata=metadata)
        ]
    )
    def solid1(_):
        return 1

    @solid(input_defs=[InputDefinition("input1", manager_key="spark_loader")])
    def solid2(_, input1):
        assert input1 == 5

    @input_manager
    def spark_table_loader(context, _resource_config):
        output = context.upstream_output
        assert output.metadata == metadata
        assert output.name == "my_output"
        assert output.step_key == "solid1"
        assert context.pipeline_name == "my_pipeline"
        assert context.solid_def.name == solid2.name
        return 5

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "my_object_manager": my_object_manager,
                    "spark_loader": spark_table_loader,
                }
            )
        ]
    )
    def my_pipeline():
        solid2(solid1())

    execute_pipeline(my_pipeline)


def test_configured():
    @input_manager(
        config_schema={"base_dir": str},
        description="abc",
        input_config_schema={"format": str},
        required_resource_keys={"r1", "r2"},
        version="123",
    )
    def my_input_manager(_):
        pass

    configured_input_manager = my_input_manager.configured({"base_dir": "/a/b/c"})

    assert isinstance(configured_input_manager, InputManagerDefinition)
    assert configured_input_manager.description == my_input_manager.description
    assert configured_input_manager.input_config_schema == my_input_manager.input_config_schema
    assert (
        configured_input_manager.required_resource_keys == my_input_manager.required_resource_keys
    )
    assert configured_input_manager.version is None


def test_input_manager_with_failure():
    _called = False

    @input_manager
    def should_fail(_, _resource_config):
        raise Failure(
            description="Foolure",
            metadata_entries=[
                EventMetadataEntry.text(label="label", text="text", description="description")
            ],
        )

    @solid
    def emit_str(_):
        return "emit"

    @solid(input_defs=[InputDefinition("_fail_input", manager_key="should_fail")])
    def fail_on_input(_, _fail_input):
        _called = True

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"should_fail": should_fail})])
    def simple():
        fail_on_input(emit_str())

    with seven.TemporaryDirectory() as tmpdir_path:

        instance = DagsterInstance.from_ref(InstanceRef.from_dir(tmpdir_path))

        result = execute_pipeline(simple, instance=instance, raise_on_error=False)

        assert not result.success

        failure_data = result.result_for_solid("fail_on_input").failure_data

        assert failure_data.error.cls_name == "Failure"

        assert failure_data.user_failure_data.description == "Foolure"
        assert failure_data.user_failure_data.metadata_entries[0].label == "label"
        assert failure_data.user_failure_data.metadata_entries[0].entry_data.text == "text"
        assert failure_data.user_failure_data.metadata_entries[0].description == "description"

        assert not _called


def test_input_manager_with_retries():
    _called = False
    _count = {"total": 0}

    @input_manager
    def should_succeed(_, _resource_config):
        if _count["total"] < 2:
            _count["total"] += 1
            raise RetryRequested(max_retries=3)
        return "foo"

    @input_manager
    def should_retry(_, _resource_config):
        raise RetryRequested(max_retries=3)

    @input_manager
    def should_not_execute(_, _resource_config):
        _called = True

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "should_succeed": should_succeed,
                    "should_not_execute": should_not_execute,
                    "should_retry": should_retry,
                }
            )
        ]
    )
    def simple():
        @solid
        def source_solid(_):
            return "foo"

        @solid(input_defs=[InputDefinition("solid_input", manager_key="should_succeed")])
        def take_input_1(_, solid_input):
            return solid_input

        @solid(input_defs=[InputDefinition("solid_input", manager_key="should_retry")])
        def take_input_2(_, solid_input):
            return solid_input

        @solid(input_defs=[InputDefinition("solid_input", manager_key="should_not_execute")])
        def take_input_3(_, solid_input):
            return solid_input

        take_input_3(take_input_2(take_input_1(source_solid())))

    with seven.TemporaryDirectory() as tmpdir_path:

        instance = DagsterInstance.from_ref(InstanceRef.from_dir(tmpdir_path))

        result = execute_pipeline(simple, instance=instance, raise_on_error=False)

        step_stats = instance.get_run_step_stats(result.run_id)
        assert len(step_stats) == 3

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
        assert _called == False
