from dagster._core.definitions.asset_condition.parent_outdated import ParentOutdatedAssetCondition
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.metadata import MetadataValue

from dagster_tests.definitions_tests.auto_materialize_tests.scenario_state import ScenarioSpec

from ..base_scenario import run_request
from .asset_condition_scenario import AssetConditionScenarioState

vee = ScenarioSpec(
    asset_specs=[
        AssetSpec(key="A0"),
        AssetSpec(key="A1", deps=["A0"]),
        AssetSpec(key="B0"),
        AssetSpec(key="B1", deps=["B0"]),
        AssetSpec(key="dummy"),
        AssetSpec(key="C", deps=["A1", "B1", "dummy"]),
    ]
)


def test_outdated_unpartitioned() -> None:
    state = AssetConditionScenarioState(
        vee, asset_condition=ParentOutdatedAssetCondition()
    ).with_runs(run_request(["A0", "A1", "B0", "B1", "dummy", "C"]))

    # all up to date
    state, result = state.evaluate_new("C")
    assert result.true_subset.size == 0

    # still true
    state, result = state.evaluate_new("C")
    assert result.true_subset.size == 0

    # for what amount to historical reasons, we only re-evaluate the condition if at least one of
    # the parent assets have been updated since the previous tick. this works in practice because
    # typically this condition is just used to filter "eager" materializations, which are always
    # in response to a parent asset being materialized, so you'll always re-evaluate this condition
    # when necessary in those cases.
    # however, this is a legitimate bug, and so in order to make this test work correctly, we need
    # to ensure that there are parent updates happening to refresh the condition status. we really
    # don't want to rely on these sorts of global rules in the future, but the "right" way of fixing
    # this would be to refresh the state of the condition if any parent anywhere upstream of it has
    # been materialized since the previous tick. However, this would cause a ton of performance
    # issues so we'll need to keep this behavior as is for now.
    # that's all to say, that's why I'm updating the dummy asset here and below
    state = state.with_runs(run_request(["dummy"]))
    # after a run of A0, C is now outdated
    state, result = state.with_runs(run_request(["A0"])).evaluate_new("C")
    assert result.true_subset.size == 1
    assert len(result.subsets_with_metadata) == 1
    subset, metadata = result.subsets_with_metadata[0]
    assert subset.size == 1
    assert metadata == {"waiting_on_parent_1": MetadataValue.asset(AssetKey("A1"))}

    # see above
    state = state.with_runs(run_request(["dummy"]))
    # after a run of B0, C is still outdated, with new metadata
    state, result = state.with_runs(run_request(["B0"])).evaluate_new("C")
    assert result.true_subset.size == 1
    assert len(result.subsets_with_metadata) == 1
    subset, metadata = result.subsets_with_metadata[0]
    assert subset.size == 1
    assert metadata == {
        "waiting_on_parent_1": MetadataValue.asset(AssetKey("A1")),
        "waiting_on_parent_2": MetadataValue.asset(AssetKey("B1")),
    }

    # after a run of A1, C is still outdated, with new metadata
    state, result = state.with_runs(run_request(["A1"])).evaluate_new("C")
    assert result.true_subset.size == 1
    assert len(result.subsets_with_metadata) == 1
    subset, metadata = result.subsets_with_metadata[0]
    assert subset.size == 1
    assert metadata == {
        "waiting_on_parent_1": MetadataValue.asset(AssetKey("B1")),
    }

    # after a run of B1, C is no longer outdated
    state, result = state.with_runs(run_request(["B1"])).evaluate_new("C")
    assert result.true_subset.size == 0
    assert len(result.subsets_with_metadata) == 0
