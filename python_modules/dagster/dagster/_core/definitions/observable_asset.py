from typing import Optional, Sequence

from dagster._core.definitions.asset_spec import (
    SYSTEM_METADATA_KEY_ASSET_VARIETAL,
    AssetSpec,
    AssetVarietal,
    ObservableAssetSpec,
)
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.definitions.events import AssetMaterialization, AssetObservation
from dagster._core.events import (
    AssetObservationData,
    DagsterEvent,
    DagsterEventType,
    EventSpecificData,
    StepMaterializationData,
)
from dagster._core.instance import DagsterInstance


def create_unexecutable_observable_assets_def(specs: Sequence[ObservableAssetSpec]):
    @multi_asset(
        specs=[
            AssetSpec(
                key=spec.key,
                description=spec.description,
                group_name=spec.group_name,
                metadata={
                    **(spec.metadata or {}),
                    **{SYSTEM_METADATA_KEY_ASSET_VARIETAL: AssetVarietal.UNEXECUTABLE.value},
                },
                deps=[dep.asset_key for dep in spec.deps],
            )
            for spec in specs
        ]
    )
    def an_asset() -> None:
        raise NotImplementedError()

    return an_asset


# Our internal guts can handle empty strings for job name and run id
# However making thse named constants for documentation, to encode where we are making the assumption,
# and to allow us to change this more easily in the future, provided we are disciplined about
# actually using this constants.
RUNLESS_JOB_NAME = ""
RUNLESS_RUN_ID = ""


def report_runless_event(
    instance: DagsterInstance, event_type: DagsterEventType, event_specific_data: EventSpecificData
) -> None:
    dagster_event = DagsterEvent(
        event_type_value=event_type.value,
        job_name=RUNLESS_JOB_NAME,
        event_specific_data=event_specific_data,
    )

    instance.report_dagster_event(dagster_event=dagster_event, run_id=RUNLESS_RUN_ID)


def report_runless_asset_materialization(
    asset_materialization: AssetMaterialization,
    instance: Optional[DagsterInstance] = None,
) -> None:
    report_runless_event(
        instance or DagsterInstance.get(),
        DagsterEventType.ASSET_MATERIALIZATION,
        StepMaterializationData(asset_materialization),
    )


def report_runless_asset_observation(
    asset_observation: AssetObservation,
    instance: Optional[DagsterInstance] = None,
) -> None:
    report_runless_event(
        instance or DagsterInstance.get(),
        DagsterEventType.ASSET_OBSERVATION,
        AssetObservationData(asset_observation),
    )
