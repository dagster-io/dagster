from typing import Iterable, Iterator, Optional

import pytest
from dagster import (
    AssetKey,
    AssetMaterialization,
    AssetObservation,
    AssetsDefinition,
    DagsterInstance,
    DagsterInvariantViolationError,
    Definitions,
    IOManager,
    Output,
    SourceAsset,
    asset,
    job,
    materialize,
    op,
)
from dagster._check import CheckError
from dagster._core.definitions.asset_spec import (
    ObservableAssetSpec,
)
from dagster._core.definitions.observable_asset import (
    create_unexecutable_observable_assets_def,
    create_unexecutable_observable_assets_def_from_source_asset,
    report_runless_asset_materialization,
    report_runless_asset_observation,
)
from dagster._core.event_api import EventLogRecord, EventRecordsFilter
from dagster._core.events import DagsterEventType
from dagster._core.execution.api import create_execution_plan


def get_latest_observation_for_asset_key(
    instance: DagsterInstance, asset_key: AssetKey
) -> Optional[EventLogRecord]:
    observations = instance.get_event_records(
        EventRecordsFilter(event_type=DagsterEventType.ASSET_OBSERVATION, asset_key=asset_key),
        limit=1,
    )

    observation = next(iter(observations), None)
    return observation


def test_observable_asset_basic_creation() -> None:
    assets_def = create_unexecutable_observable_assets_def(
        specs=[
            ObservableAssetSpec(
                key="observable_asset_one",
                # multi-asset does not support description lol
                # description="desc",
                metadata={"user_metadata": "value"},
                group_name="a_group",
            )
        ]
    )
    assert isinstance(assets_def, AssetsDefinition)

    expected_key = AssetKey(["observable_asset_one"])

    assert assets_def.key == expected_key
    # assert assets_def.descriptions_by_key[expected_key] == "desc"
    assert assets_def.metadata_by_key[expected_key]["user_metadata"] == "value"
    assert assets_def.group_names_by_key[expected_key] == "a_group"
    assert assets_def.is_asset_executable(expected_key) is False


def test_normal_asset_materializeable() -> None:
    @asset
    def an_asset() -> None: ...

    assert an_asset.is_asset_executable(AssetKey(["an_asset"])) is True


def test_observable_asset_creation_with_deps() -> None:
    asset_two = ObservableAssetSpec("observable_asset_two")
    assets_def = create_unexecutable_observable_assets_def(
        specs=[
            ObservableAssetSpec(
                "observable_asset_one",
                deps=[asset_two.key],  # todo remove key when asset deps accepts it
            )
        ]
    )
    assert isinstance(assets_def, AssetsDefinition)

    expected_key = AssetKey(["observable_asset_one"])

    assert assets_def.key == expected_key
    assert assets_def.asset_deps[expected_key] == {
        AssetKey(["observable_asset_two"]),
    }


def test_report_runless_materialization() -> None:
    instance = DagsterInstance.ephemeral()

    report_runless_asset_materialization(
        asset_materialization=AssetMaterialization(asset_key="observable_asset_one"),
        instance=instance,
    )

    mat_event = instance.get_latest_materialization_event(
        asset_key=AssetKey("observable_asset_one")
    )

    assert mat_event
    assert mat_event.asset_materialization
    assert mat_event.asset_materialization.asset_key == AssetKey("observable_asset_one")


def test_report_runless_observation() -> None:
    instance = DagsterInstance.ephemeral()

    report_runless_asset_observation(
        asset_observation=AssetObservation(asset_key="observable_asset_one"),
        instance=instance,
    )

    observation = get_latest_observation_for_asset_key(
        instance, asset_key=AssetKey("observable_asset_one")
    )
    assert observation

    assert observation.asset_key == AssetKey("observable_asset_one")


def test_emit_asset_observation_in_user_space() -> None:
    # This test to exists to demonstrate that you cannot emit an asset observation without
    # it automatically emitting a materialization because of the None output. We will have
    # to fix this because being able to supplant observable source assets

    @asset(key="asset_in_user_space")
    def active_observable_asset_in_user_space() -> Iterator:
        # not ideal but it works
        yield AssetObservation(asset_key="asset_in_user_space", metadata={"foo": "bar"})
        yield Output(None)

    instance = DagsterInstance.ephemeral()

    # to avoid breaking your brain, think of this as "execute" or "refresh", not "materialize"
    assert materialize(assets=[active_observable_asset_in_user_space], instance=instance).success

    observation = get_latest_observation_for_asset_key(
        instance, asset_key=AssetKey("asset_in_user_space")
    )
    assert observation
    assert observation.asset_key == AssetKey("asset_in_user_space")

    mat_event = instance.get_latest_materialization_event(asset_key=AssetKey("asset_in_user_space"))

    # we actually want this to be false once we make changes to make mainline assets
    # replace observable source assets
    assert mat_event


def test_executable_upstream_of_nonexecutable_illegal() -> None:
    pass

    @asset
    def upstream_asset() -> None: ...

    downstream_asset = create_unexecutable_observable_assets_def(
        specs=[
            ObservableAssetSpec(
                "downstream_asset",
                deps=[upstream_asset],
            )
        ]
    )

    with pytest.raises(DagsterInvariantViolationError) as exc_info:
        Definitions(assets=[upstream_asset, downstream_asset])

    assert (
        "An executable asset cannot be upstream of a non-executable asset. Non-executable asset"
        ' "downstream_asset" downstream of executable asset "upstream_asset"'
        in str(exc_info.value)
    )


def test_execute_job_that_implicitly_includes_non_executable_asset() -> None:
    upstream_asset = create_unexecutable_observable_assets_def(
        specs=[
            ObservableAssetSpec(
                "upstream_asset",
            )
        ]
    )

    @asset(deps=[upstream_asset])
    def downstream_asset() -> None: ...

    defs = Definitions(assets=[upstream_asset, downstream_asset])

    assert (
        defs.get_implicit_global_asset_job_def()
        .execute_in_process(instance=DagsterInstance.ephemeral())
        .success
    )

    with pytest.raises(CheckError) as exc_info:
        create_execution_plan(defs.get_implicit_global_asset_job_def())

    assert "Cannot pass unexecutable assets defs to create_execution_plan with keys:" in str(
        exc_info.value
    )


def test_execute_job_that_explicitly_includes_non_executable_asset() -> None:
    upstream_asset = create_unexecutable_observable_assets_def(
        specs=[
            ObservableAssetSpec(
                "upstream_asset",
            )
        ]
    )

    @asset(deps=[upstream_asset])
    def downstream_asset() -> None: ...

    defs = Definitions(assets=[upstream_asset, downstream_asset])

    with pytest.raises(DagsterInvariantViolationError) as exc_info:
        defs.get_implicit_global_asset_job_def().execute_in_process(
            instance=DagsterInstance.ephemeral(), asset_selection=[upstream_asset.key]
        )

    assert (
        'You have attempted to explicitly select asset "upstream_asset" for execution.'
        " This is not allowed as it is not executable."
        in str(exc_info.value)
    )


def test_demonstrate_op_job_over_observable_assets() -> None:
    @op
    def an_op_that_emits() -> Iterable:
        yield AssetMaterialization(asset_key="asset_one")
        yield Output(None)

    @job
    def a_job_that_emits() -> None:
        an_op_that_emits()

    instance = DagsterInstance.ephemeral()

    asset_one = create_unexecutable_observable_assets_def([ObservableAssetSpec("asset_one")])

    defs = Definitions(assets=[asset_one], jobs=[a_job_that_emits])

    assert defs.get_job_def("a_job_that_emits").execute_in_process(instance=instance).success

    mat_event = instance.get_latest_materialization_event(asset_key=AssetKey("asset_one"))

    assert mat_event
    assert mat_event.asset_materialization
    assert mat_event.asset_materialization.asset_key == AssetKey("asset_one")


def test_how_source_assets_are_backwards_compatible() -> None:
    class DummyIOManager(IOManager):
        def handle_output(self, context, obj) -> None:
            pass

        def load_input(self, context) -> str:
            return "hardcoded"

    source_asset = SourceAsset(key="source_asset", io_manager_def=DummyIOManager())

    @asset
    def an_asset(source_asset: str) -> str:
        return "hardcoded" + "-computed"

    defs_with_source = Definitions(assets=[source_asset, an_asset])

    instance = DagsterInstance.ephemeral()

    result_one = defs_with_source.get_implicit_global_asset_job_def().execute_in_process(
        instance=instance
    )

    assert result_one.success
    assert result_one.output_for_node("an_asset") == "hardcoded-computed"

    defs_with_shim = Definitions(
        assets=[create_unexecutable_observable_assets_def_from_source_asset(source_asset), an_asset]
    )

    result_two = defs_with_shim.get_implicit_global_asset_job_def().execute_in_process(
        instance=instance
    )

    assert result_two.success
    assert result_two.output_for_node("an_asset") == "hardcoded-computed"


def test_direct_passing_of_observable_asset_spec_to_definitions() -> None:
    defs = Definitions(
        assets=[
            ObservableAssetSpec(
                key="observable_asset_one",
                # multi-asset does not support description lol
                # description="desc",
                metadata={"user_metadata": "value"},
                group_name="a_group",
            )
        ]
    )

    assert defs.get_asset_graph().assets_def_for_key("observable_asset_one")
