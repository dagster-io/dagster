from dagster import Definitions, materialize, sensor
from dagster._core.definitions.asset_spec import ObservableAssetSpec
from dagster._core.definitions.data_version import DataVersion
from dagster._core.definitions.events import AssetMaterialization, AssetObservation
from dagster._core.definitions.sensor_definition import SensorEvaluationContext

from external_lib import (
    report_asset_materialization,
    report_asset_observation,
)


@sensor()
def sensor_that_emits_materializations(context: SensorEvaluationContext):
    report_asset_materialization(
        instance=context.instance,
        asset_materialization=AssetMaterialization(
            asset_key="observable_asset_one", metadata={"source": "from_sensor"}
        ),
    )


@sensor()
def sensor_that_observes(context: SensorEvaluationContext):
    report_asset_observation(
        instance=context.instance,
        asset_observation=AssetObservation(
            asset_key="observable_asset_one", metadata={"source": "from_sensor"}
        ),
    )


def observable_asset(fn, **kwargs):
    return fn


def observe_function():
    yield DataVersion("a_version")


# todo move out of decorator and push down
# @asset(materializeable=False)
# def actively_observed_asset():
#     yield from observe_function()


@sensor()
def an_observing_sensor():
    yield from observe_function()

# @observable_asset
# # This function is invocable in the context of a sensor _or_ a run
# def actively_observed_asset():
#     yield DataVersion("a_version")

# This code location defines metadata exclusively. It expects execution to happen elsewhere.
asset_one = ObservableAssetSpec(key="observable_asset_one")
asset_two = ObservableAssetSpec(key="observable_asset_two", deps=[asset_one])
# defs = Definitions(assets=[asset_one, asset_two, actively_observed_asset])




defs = Definitions(
    assets=[asset_one, asset_two],
    # assets=[actively_observed_asset],
    # sensors=[actively_observed_asset.to_sensor(...)],  # could do sensory things here
)


# sensors=[sensor_that_emits_materializations, sensor_that_observes],

# actively_observed_asset()

materialize(defs.get_asset_graph().assets)
