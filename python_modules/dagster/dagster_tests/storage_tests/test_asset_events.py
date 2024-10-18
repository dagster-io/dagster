from dagster import (
    AssetKey,
    AssetObservation,
    In,
    StaticPartitionsDefinition,
    asset,
    build_input_context,
    job,
    materialize,
    op,
)
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetLineageInfo
from dagster._core.events import DagsterEventType
from dagster._core.instance import DagsterInstance
from dagster._core.storage.input_manager import input_manager
from dagster._core.storage.io_manager import IOManager


def n_asset_keys(path, n):
    return AssetLineageInfo(AssetKey(path), set([str(i) for i in range(n)]))


def check_materialization(materialization, asset_key, parent_assets=None, metadata=None):
    event_data = materialization.event_specific_data
    assert event_data.materialization.asset_key == asset_key
    assert sorted(event_data.materialization.metadata) == metadata or {}
    assert event_data.asset_lineage == (parent_assets or [])


def test_io_manager_add_input_metadata():
    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            context.add_input_metadata(metadata={"foo": "bar"})
            context.add_input_metadata(metadata={"baz": "qux"})

            observations = context.get_observations()
            assert observations[0].asset_key == context.asset_key
            assert "foo" in observations[0].metadata
            assert "baz" in observations[1].metadata
            return 1

    @asset
    def before(): ...

    @asset
    def after(before):
        del before

    get_observation = lambda event: event.event_specific_data.asset_observation

    result = materialize([before, after], resources={"io_manager": MyIOManager()})
    observations = [
        event for event in result.all_node_events if event.event_type_value == "ASSET_OBSERVATION"
    ]

    # first observation
    assert observations[0].step_key == "after"
    assert get_observation(observations[0]) == AssetObservation(
        asset_key=before.key, metadata={"foo": "bar"}
    )
    # second observation
    assert observations[1].step_key == "after"
    assert get_observation(observations[1]) == AssetObservation(
        asset_key=before.key, metadata={"baz": "qux"}
    )

    # confirm loaded_input event contains metadata
    loaded_input_event = next(
        event for event in result.all_events if event.event_type_value == "LOADED_INPUT"
    )
    assert loaded_input_event
    loaded_input_event_metadata = loaded_input_event.event_specific_data.metadata
    assert len(loaded_input_event_metadata) == 2
    assert "foo" in loaded_input_event_metadata
    assert "baz" in loaded_input_event_metadata


def test_input_manager_add_input_metadata():
    @input_manager
    def my_input_manager(context):
        context.add_input_metadata(metadata={"foo": "bar"})
        context.add_input_metadata(metadata={"baz": "qux"})
        return []

    @op(ins={"input1": In(input_manager_key="my_input_manager")})
    def my_op(_, input1):
        return input1

    @job(resource_defs={"my_input_manager": my_input_manager})
    def my_job():
        my_op()

    result = my_job.execute_in_process()
    loaded_input_event = next(
        event for event in result.all_events if event.event_type_value == "LOADED_INPUT"
    )
    metadata = loaded_input_event.event_specific_data.metadata
    assert len(metadata) == 2
    assert "foo" in metadata
    assert "baz" in metadata


def test_io_manager_single_partition_add_input_metadata():
    partitions_def = StaticPartitionsDefinition(["a", "b", "c"])

    @asset(partitions_def=partitions_def)
    def asset_1():
        return 1

    @asset(partitions_def=partitions_def)
    def asset_2(asset_1):
        return asset_1 + 1

    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            context.add_input_metadata(metadata={"foo": "bar"}, description="hello world")
            return 1

    result = materialize(
        [asset_1, asset_2], resources={"io_manager": MyIOManager()}, partition_key="a"
    )

    get_observation = lambda event: event.event_specific_data.asset_observation

    observations = [
        event for event in result.all_node_events if event.event_type_value == "ASSET_OBSERVATION"
    ]

    assert observations[0].step_key == "asset_2"
    assert get_observation(observations[0]) == AssetObservation(
        asset_key="asset_1",
        metadata={"foo": "bar"},
        description="hello world",
        partition="a",
    )


def test_build_input_context_add_input_metadata():
    @op
    def my_op():
        pass

    context = build_input_context(op_def=my_op)
    context.add_input_metadata({"foo": "bar"})


def test_asset_materialization_accessors():
    @asset
    def return_one():
        return 1

    with DagsterInstance.ephemeral() as instance:
        defs = Definitions(assets=[return_one])
        defs.get_implicit_global_asset_job_def().execute_in_process(instance=instance)

        log_entry = instance.get_latest_materialization_event(AssetKey("return_one"))
        assert log_entry
        assert log_entry.asset_materialization
        assert log_entry.asset_materialization.asset_key == AssetKey("return_one")

        # test when it is not a materilization event
        records = [
            *instance.fetch_run_status_changes(DagsterEventType.RUN_SUCCESS, limit=1).records
        ]
        assert len(records) == 1
        assert records[0].event_log_entry
        assert records[0].event_log_entry.asset_materialization is None
