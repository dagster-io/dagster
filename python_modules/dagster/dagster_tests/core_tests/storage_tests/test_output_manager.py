import pytest
from dagster import (
    AssetMaterialization,
    DagsterInstance,
    DagsterInvalidDefinitionError,
    DagsterType,
    EventMetadataEntry,
    Failure,
    InputDefinition,
    ModeDefinition,
    ObjectManager,
    Output,
    OutputDefinition,
    OutputManagerDefinition,
    RetryRequested,
    dagster_type_materializer,
    execute_pipeline,
    object_manager,
    pipeline,
    seven,
    solid,
)
from dagster.core.instance import InstanceRef
from dagster.core.storage.input_manager import input_manager
from dagster.core.storage.output_manager import output_manager


def test_output_manager():
    adict = {}

    @output_manager
    def my_output_manager(_context, _resource_config, obj):
        adict["result"] = obj

    @solid(output_defs=[OutputDefinition(manager_key="my_output_manager")])
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
    def my_output_manager(context, _resource_config, obj):
        adict["result"] = (context.config, obj)

    @solid(output_defs=[OutputDefinition(name="my_output", manager_key="my_output_manager")])
    def my_solid(_):
        return 5

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"my_output_manager": my_output_manager})])
    def my_pipeline():
        my_solid()

    execute_pipeline(
        my_pipeline, run_config={"solids": {"my_solid": {"outputs": {"my_output": "a"}}}}
    )

    assert adict["result"] == ("a", 5)


@pytest.mark.xfail(
    reason="""This test fails during the intermediate state we're in where output managers have
        been introduced, but they haven't yet been consolidated with asset stores. After the
        consolidation, there will be no more asset store attached to the output of my_solid."""
)
def test_output_manager_no_input_manager():
    adict = {}

    @output_manager
    def my_output_manager(_context, _resource_config, obj):
        adict["result"] = obj

    @solid(output_defs=[OutputDefinition(manager_key="my_output_manager")])
    def my_solid(_):
        return 5

    @solid
    def my_downstream_solid(_, input1):
        return input1 + 1

    with pytest.raises(DagsterInvalidDefinitionError):

        @pipeline(
            mode_defs=[ModeDefinition(resource_defs={"my_output_manager": my_output_manager})]
        )
        def my_pipeline():
            my_downstream_solid(my_solid())

        assert my_pipeline


def test_separate_output_manager_input_manager():
    adict = {}

    @output_manager
    def my_output_manager(_context, _resource_config, obj):
        adict["result"] = obj

    @input_manager
    def my_input_manager(_context, _resource_config):
        return adict["result"]

    @solid(output_defs=[OutputDefinition(manager_key="my_output_manager")])
    def my_solid(_):
        return 5

    @solid(input_defs=[InputDefinition("input1", manager_key="my_input_manager")])
    def my_downstream_solid(_, input1):
        return input1 + 1

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "my_input_manager": my_input_manager,
                    "my_output_manager": my_output_manager,
                }
            )
        ]
    )
    def my_pipeline():
        my_downstream_solid(my_solid())

    execute_pipeline(my_pipeline)

    assert adict["result"] == 5


def test_type_materializer_and_configurable_output_manager():
    @dagster_type_materializer(config_schema={"type_materializer_path": str})
    def my_materializer(_, _config, _value):
        assert False, "shouldn't get here"

    adict = {}

    @output_manager(output_config_schema={"output_manager_path": str})
    def my_output_manager(_context, _resource_config, obj):
        adict["result"] = obj

    my_type = DagsterType(lambda _, _val: True, name="my_type", materializer=my_materializer)

    @solid(
        output_defs=[
            OutputDefinition(name="output1", manager_key="my_output_manager", dagster_type=my_type),
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
    def my_output_manager(_context, _resource_config, obj):
        adict["result"] = obj

    my_type = DagsterType(lambda _, _val: True, name="my_type", materializer=my_materializer)

    @solid(
        output_defs=[
            OutputDefinition(name="output1", manager_key="my_output_manager", dagster_type=my_type),
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
    _called = False

    @output_manager
    def should_fail(_, _resource_config, _obj):
        raise Failure(
            description="Foolure",
            metadata_entries=[
                EventMetadataEntry.text(label="label", text="text", description="description")
            ],
        )

    @solid(output_defs=[OutputDefinition(manager_key="should_fail")])
    def emit_str(_):
        return "emit"

    @solid(input_defs=[InputDefinition(name="_input_str", dagster_type=str)])
    def should_not_call(_, _input_str):
        _called = True

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"should_fail": should_fail})])
    def simple():
        should_not_call(emit_str())

    with seven.TemporaryDirectory() as tmpdir_path:

        instance = DagsterInstance.from_ref(InstanceRef.from_dir(tmpdir_path))

        result = execute_pipeline(simple, instance=instance, raise_on_error=False)

        assert not result.success

        failure_data = result.result_for_solid("emit_str").failure_data

        assert failure_data.error.cls_name == "Failure"

        assert failure_data.user_failure_data.description == "Foolure"
        assert failure_data.user_failure_data.metadata_entries[0].label == "label"
        assert failure_data.user_failure_data.metadata_entries[0].entry_data.text == "text"
        assert failure_data.user_failure_data.metadata_entries[0].description == "description"

        assert not _called


def test_output_manager_with_retries():
    _called = False
    _count = {"total": 0}

    @object_manager
    def should_succeed(_):
        class FakeObjectManager(ObjectManager):
            def load_input(self, _context):
                return "foo"

            def handle_output(self, _context, _obj):
                if _count["total"] < 2:
                    _count["total"] += 1
                    raise RetryRequested(max_retries=3)

        return FakeObjectManager()

    @object_manager
    def should_retry(_):
        class FakeObjectManager(ObjectManager):
            def load_input(self, _context):
                return "foo"

            def handle_output(self, _context, _obj):
                raise RetryRequested(max_retries=3)

        return FakeObjectManager()

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={"should_succeed": should_succeed, "should_retry": should_retry,}
            )
        ]
    )
    def simple():
        @solid(output_defs=[OutputDefinition(manager_key="should_succeed")],)
        def source_solid(_):
            return "foo"

        @solid(
            input_defs=[InputDefinition("solid_input")],
            output_defs=[OutputDefinition(manager_key="should_retry")],
        )
        def take_input(_, solid_input):
            return solid_input

        @solid(input_defs=[InputDefinition("_solid_input")])
        def should_not_execute(_, _solid_input):
            _called = True

        should_not_execute(take_input(source_solid()))

    with seven.TemporaryDirectory() as tmpdir_path:

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
