import dataclasses
import datetime
import json
import logging
import os
import sys
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import AbstractSet, Iterable, NamedTuple, Optional, Sequence, Union, cast

import mock
from dagster import (
    AssetExecutionContext,
    AssetKey,
    AssetsDefinition,
    AssetSpec,
    AutoMaterializePolicy,
    DagsterRunStatus,
    Definitions,
    PartitionsDefinition,
    RunRequest,
    RunsFilter,
    SensorDefinition,
    asset,
    multi_asset,
    op,
)
from dagster._core.definitions import materialize
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.asset_spec import (
    SYSTEM_METADATA_KEY_ASSET_EXECUTION_TYPE,
    AssetExecutionType,
)
from dagster._core.definitions.data_version import DATA_VERSION_TAG
from dagster._core.definitions.definitions_class import create_repository_using_definitions_args
from dagster._core.definitions.events import (
    AssetMaterialization,
    AssetObservation,
    CoercibleToAssetKey,
)
from dagster._core.definitions.executor_definition import in_process_executor
from dagster._core.definitions.repository_definition.repository_definition import (
    RepositoryDefinition,
)
from dagster._core.definitions.repository_definition.valid_definitions import (
    SINGLETON_REPOSITORY_NAME,
)
from dagster._core.execution.api import create_execution_plan
from dagster._core.instance import DagsterInstance
from dagster._core.remote_representation.external_data import external_repository_data_from_def
from dagster._core.remote_representation.origin import InProcessCodeLocationOrigin
from dagster._core.storage.tags import PARTITION_NAME_TAG
from dagster._core.test_utils import (
    InProcessTestWorkspaceLoadTarget,
    create_test_daemon_workspace_context,
    freeze_time,
)
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.utils import make_new_run_id
from dagster._serdes.utils import create_snapshot_id
from dagster._time import datetime_from_timestamp, get_current_datetime, parse_time_string
from typing_extensions import Self

from .base_scenario import run_request

FAIL_TAG = "test/fail"


def get_code_location_origin(
    scenario_spec: "ScenarioSpec",
    location_name="test_location",
    repository_name=SINGLETON_REPOSITORY_NAME,
) -> InProcessCodeLocationOrigin:
    """Hacky method to allow us to point a code location at a module-scoped attribute, even though
    the attribute is not defined until the scenario is run.
    """
    repository = create_repository_using_definitions_args(
        name=repository_name,
        assets=scenario_spec.assets,
        executor=in_process_executor,
        sensors=scenario_spec.sensors,
    )

    return _get_code_location_origin_from_repository(
        cast(RepositoryDefinition, repository), location_name=location_name
    )


def _get_code_location_origin_from_repository(repository: RepositoryDefinition, location_name: str):
    attribute_name = (
        f"_asset_daemon_target_{create_snapshot_id(external_repository_data_from_def(repository))}"
    )

    if attribute_name not in globals():
        globals()[attribute_name] = repository

    return InProcessCodeLocationOrigin(
        loadable_target_origin=LoadableTargetOrigin(
            executable_path=sys.executable,
            module_name=(
                "dagster_tests.definitions_tests.declarative_automation_tests.scenario_utils.scenario_state"
            ),
            working_directory=os.getcwd(),
            attribute=attribute_name,
        ),
        location_name=location_name,
    )


class MultiAssetSpec(NamedTuple):
    specs: Sequence[AssetSpec]
    partitions_def: Optional[PartitionsDefinition] = None
    can_subset: bool = False


@dataclass(frozen=True)
class ScenarioSpec:
    """A construct for declaring and modifying a desired Definitions object."""

    asset_specs: Sequence[Union[AssetSpec, MultiAssetSpec]]
    current_time: datetime.datetime = field(default_factory=lambda: get_current_datetime())
    sensors: Sequence[SensorDefinition] = field(default_factory=list)
    additional_repo_specs: Sequence["ScenarioSpec"] = field(default_factory=list)

    def with_sensors(self, sensors: Sequence[SensorDefinition]) -> "ScenarioSpec":
        return dataclasses.replace(self, sensors=sensors)

    @property
    def assets(self) -> Sequence[AssetsDefinition]:
        def compute_fn(context: AssetExecutionContext) -> None:
            fail_keys = {
                AssetKey.from_coercible(s)
                for s in json.loads(context.run.tags.get(FAIL_TAG) or "[]")
            }
            for asset_key in context.selected_asset_keys:
                if asset_key in fail_keys:
                    raise Exception("Asset failed")

        assets = []
        for spec in self.asset_specs:
            if isinstance(spec, MultiAssetSpec):

                @multi_asset(**spec._asdict())
                def _multi_asset(context: AssetExecutionContext):
                    return compute_fn(context)

                assets.append(_multi_asset)
            else:
                execution_type_str = spec.metadata.get(SYSTEM_METADATA_KEY_ASSET_EXECUTION_TYPE)
                execution_type = (
                    AssetExecutionType[execution_type_str] if execution_type_str else None
                )
                # create an observable_source_asset or regular asset depending on the execution type
                if execution_type == AssetExecutionType.OBSERVATION:

                    @op
                    def noop(): ...

                    osa = AssetsDefinition(
                        specs=[spec],
                        execution_type=execution_type,
                        keys_by_output_name={"result": spec.key},
                        node_def=noop,
                    )

                    assets.append(osa)
                else:
                    # strip out the relevant paramters from the spec
                    params = {
                        "key",
                        "deps",
                        "group_name",
                        "code_version",
                        "automation_condition",
                        "freshness_policy",
                        "partitions_def",
                        "metadata",
                    }

                    assets.append(
                        asset(
                            compute_fn=compute_fn,
                            **{k: v for k, v in spec._asdict().items() if k in params},
                        )
                    )

        return assets

    @property
    def defs(self) -> Definitions:
        return Definitions(assets=self.assets, sensors=self.sensors)

    @property
    def asset_graph(self) -> AssetGraph:
        return AssetGraph.from_assets(self.assets)

    def with_additional_repositories(
        self,
        scenario_specs: Sequence["ScenarioSpec"],
    ) -> "ScenarioSpec":
        return dataclasses.replace(
            self, additional_repo_specs=[*self.additional_repo_specs, *scenario_specs]
        )

    def with_current_time(self, time: Union[str, datetime.datetime]) -> "ScenarioSpec":
        if isinstance(time, str):
            time = parse_time_string(time)
        return dataclasses.replace(self, current_time=time)

    def with_current_time_advanced(self, **kwargs) -> "ScenarioSpec":
        # hacky support for adding years
        if "years" in kwargs:
            kwargs["days"] = kwargs.get("days", 0) + 365 * kwargs.pop("years")
        return dataclasses.replace(
            self, current_time=self.current_time + datetime.timedelta(**kwargs)
        )

    def with_asset_properties(
        self, keys: Optional[Iterable[CoercibleToAssetKey]] = None, **kwargs
    ) -> "ScenarioSpec":
        """Convenience method to update the properties of one or more assets in the scenario state."""
        new_asset_specs = []
        if "auto_materialize_policy" in kwargs:
            policy = kwargs.pop("auto_materialize_policy")
            kwargs["automation_condition"] = policy.to_automation_condition() if policy else None
        for spec in self.asset_specs:
            if isinstance(spec, MultiAssetSpec):
                partitions_def = kwargs.get("partitions_def", spec.partitions_def)
                new_multi_specs = [
                    s._replace(**{k: v for k, v in kwargs.items() if k != "partitions_def"})
                    if keys is None or s.key in keys
                    else s
                    for s in spec.specs
                ]
                new_asset_specs.append(
                    spec._replace(partitions_def=partitions_def, specs=new_multi_specs)
                )
            else:
                if keys is None or spec.key in {AssetKey.from_coercible(key) for key in keys}:
                    new_asset_specs.append(spec._replace(**kwargs))
                else:
                    new_asset_specs.append(spec)
        return dataclasses.replace(self, asset_specs=new_asset_specs)

    def with_all_eager(self, max_materializations_per_minute: int = 1) -> "ScenarioSpec":
        return self.with_asset_properties(
            auto_materialize_policy=AutoMaterializePolicy.eager(
                max_materializations_per_minute=max_materializations_per_minute,
            )
        )


@dataclass(frozen=True)
class ScenarioState:
    """A reference to the state of a specific scenario alongside an instance."""

    scenario_spec: ScenarioSpec
    instance: DagsterInstance = field(default_factory=lambda: DagsterInstance.ephemeral())
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger(__name__))

    @property
    def current_time(self) -> datetime.datetime:
        return self.scenario_spec.current_time

    @property
    def asset_graph(self) -> AssetGraph:
        return self.scenario_spec.asset_graph

    def with_current_time(self, time: Union[str, datetime.datetime]) -> Self:
        return dataclasses.replace(self, scenario_spec=self.scenario_spec.with_current_time(time))

    def with_current_time_advanced(self, **kwargs) -> Self:
        return dataclasses.replace(
            self, scenario_spec=self.scenario_spec.with_current_time_advanced(**kwargs)
        )

    def with_asset_properties(
        self, keys: Optional[Iterable[CoercibleToAssetKey]] = None, **kwargs
    ) -> Self:
        return dataclasses.replace(
            self, scenario_spec=self.scenario_spec.with_asset_properties(keys, **kwargs)
        )

    def _with_run_with_status_for_assets(
        self,
        asset_keys: AbstractSet[AssetKey],
        partition_key: Optional[str],
        status: DagsterRunStatus,
    ) -> Self:
        run_id = make_new_run_id()
        with freeze_time(self.current_time):
            job_def = self.scenario_spec.defs.get_implicit_job_def_for_assets(
                asset_keys=list(asset_keys)
            )
            assert job_def
            execution_plan = create_execution_plan(job_def, run_config={})
            self.instance.create_run_for_job(
                job_def=job_def,
                run_id=run_id,
                status=status,
                asset_selection=frozenset(asset_keys),
                execution_plan=execution_plan,
                tags={PARTITION_NAME_TAG: partition_key} if partition_key else None,
            )
            assert self.instance.get_run_by_id(run_id)
        return self

    def with_in_progress_run_for_asset(
        self, asset_key: CoercibleToAssetKey, partition_key: Optional[str] = None
    ) -> Self:
        asset_key = AssetKey.from_coercible(asset_key)
        return self._with_run_with_status_for_assets(
            asset_keys={asset_key}, partition_key=partition_key, status=DagsterRunStatus.STARTED
        )

    def with_failed_run_for_asset(
        self, asset_key: CoercibleToAssetKey, partition_key: Optional[str] = None
    ) -> Self:
        asset_key = AssetKey.from_coercible(asset_key)
        return self._with_run_with_status_for_assets(
            asset_keys={asset_key}, partition_key=partition_key, status=DagsterRunStatus.FAILURE
        )

    def with_runs(self, *run_requests: RunRequest) -> Self:
        start = datetime.datetime.now()

        def test_time_fn() -> float:
            # this function will increment the current timestamp in real time, relative to the
            # fake current_time on the scenario state
            return (self.current_time + (datetime.datetime.now() - start)).timestamp()

        with freeze_time(self.current_time), mock.patch("time.time", new=test_time_fn):
            for rr in run_requests:
                materialize(
                    assets=self.scenario_spec.assets,
                    instance=self.instance,
                    partition_key=rr.partition_key,
                    tags=rr.tags,
                    raise_on_error=False,
                    selection=rr.asset_selection,
                )
        # increment current_time by however much time elapsed during the materialize call
        return dataclasses.replace(
            self,
            scenario_spec=self.scenario_spec.with_current_time(
                datetime_from_timestamp(test_time_fn())
            ),
        )

    def with_reported_materialization(
        self, asset_key: CoercibleToAssetKey, partition_key: Optional[str] = None
    ) -> Self:
        mat = AssetMaterialization(
            asset_key=asset_key,
            partition=partition_key,
        )
        self.instance.report_runless_asset_event(mat)
        return self

    def with_reported_observation(
        self,
        asset_key: CoercibleToAssetKey,
        partition_key: Optional[str] = None,
        data_version: Optional[str] = None,
    ) -> Self:
        obs = AssetObservation(
            asset_key=asset_key,
            partition=partition_key,
            tags={DATA_VERSION_TAG: data_version} if data_version else None,
        )
        self.instance.report_runless_asset_event(obs)
        return self

    def _with_runs_with_status(self, status: DagsterRunStatus) -> Self:
        """Create new runs that will run to completion for all existing runs with the given status,
        and delete the runs with that status from the instance.
        This allows us to "freeze" runs in a particular state to help observe how conditions react
        to certain statuses, then have them complete at a time of our choosing.
        """
        runs = self.instance.get_runs(filters=RunsFilter(statuses=[status]))
        for run in runs:
            self.instance.delete_run(run_id=run.run_id)
        return self.with_runs(
            *[
                run_request(
                    asset_keys=list(run.asset_selection or set()),
                    partition_key=run.tags.get(PARTITION_NAME_TAG),
                )
                for run in runs
            ]
        )

    def with_not_started_runs(self) -> Self:
        return self._with_runs_with_status(DagsterRunStatus.NOT_STARTED)

    def with_in_progress_runs_completed(self) -> Self:
        return self._with_runs_with_status(DagsterRunStatus.STARTED)

    def with_dynamic_partitions(
        self, partitions_def_name: str, partition_keys: Sequence[str]
    ) -> Self:
        self.instance.add_dynamic_partitions(
            partitions_def_name=partitions_def_name, partition_keys=partition_keys
        )
        return self

    def start_sensor(self, sensor_name: str) -> Self:
        with self._get_external_sensor(sensor_name) as sensor:
            self.instance.start_sensor(sensor)
        return self

    def stop_sensor(self, sensor_name: str) -> Self:
        with self._get_external_sensor(sensor_name) as sensor:
            self.instance.stop_sensor(sensor.get_external_origin_id(), sensor.selector_id, sensor)
        return self

    @contextmanager
    def _get_external_sensor(self, sensor_name):
        with self._create_workspace_context() as workspace_context:
            workspace = workspace_context.create_request_context()
            sensor = next(
                iter(workspace.get_code_location("test_location").get_repositories().values())
            ).get_external_sensor(sensor_name)
            assert sensor
            yield sensor

    @contextmanager
    def _create_workspace_context(self):
        origins = [
            _get_code_location_origin_from_repository(
                scenario_spec.defs.get_repository_def(), f"extra_location_{i}"
            )
            for i, scenario_spec in enumerate(self.scenario_spec.additional_repo_specs)
        ] + [get_code_location_origin(self.scenario_spec)]

        target = InProcessTestWorkspaceLoadTarget(origins)
        with create_test_daemon_workspace_context(
            workspace_load_target=target, instance=self.instance
        ) as workspace_context:
            yield workspace_context
