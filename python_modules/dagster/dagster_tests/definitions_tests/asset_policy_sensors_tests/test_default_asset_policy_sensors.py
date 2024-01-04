from unittest.mock import MagicMock

import pytest
from dagster import (
    AssetKey,
    AutoMaterializePolicy,
    Definitions,
    SkipReason,
    asset,
    observable_source_asset,
    sensor,
)
from dagster._core.definitions.automation_policy_sensor_definition import (
    AutomationPolicySensorDefinition,
)
from dagster._core.definitions.external_asset_graph import ExternalAssetGraph
from dagster._core.definitions.sensor_definition import (
    SensorType,
)
from dagster._core.host_representation.external import ExternalRepository
from dagster._core.host_representation.external_data import external_repository_data_from_def
from dagster._core.host_representation.handle import RepositoryHandle
from dagster._core.host_representation.origin import (
    ExternalRepositoryOrigin,
    RegisteredCodeLocationOrigin,
)
from dagster._core.test_utils import instance_for_test


@asset(auto_materialize_policy=AutoMaterializePolicy.eager())
def auto_materialize_asset():
    pass


@asset(auto_materialize_policy=AutoMaterializePolicy.eager())
def other_auto_materialize_asset():
    pass


@observable_source_asset(auto_observe_interval_minutes=1)
def auto_observe_asset():
    pass


@observable_source_asset(auto_observe_interval_minutes=1)
def other_auto_observe_asset():
    pass


@asset
def boring_asset():
    pass


@observable_source_asset
def boring_observable_asset():
    pass


@sensor()
def normal_sensor():
    yield SkipReason("OOPS")


defs = Definitions(
    assets=[
        auto_materialize_asset,
        other_auto_materialize_asset,
        auto_observe_asset,
        other_auto_observe_asset,
        boring_asset,
        boring_observable_asset,
    ],
    sensors=[normal_sensor],
)


@pytest.fixture
def instance_with_automation_policy_sensors():
    with instance_for_test(
        {"auto_materialize": {"use_automation_policy_sensors": True}}
    ) as the_instance:
        yield the_instance


@pytest.fixture
def instance_without_automation_policy_sensors():
    with instance_for_test() as the_instance:
        yield the_instance


def test_default_automation_policy_sensors(instance_with_automation_policy_sensors):
    instance = instance_with_automation_policy_sensors

    repo_handle = MagicMock(spec=RepositoryHandle)
    repo_handle.get_external_origin.return_value = ExternalRepositoryOrigin(
        code_location_origin=RegisteredCodeLocationOrigin(location_name="foo_location"),
        repository_name="bar_repo",
    )

    external_repo = ExternalRepository(
        external_repository_data_from_def(
            defs.get_repository_def(),
        ),
        repository_handle=repo_handle,
        instance=instance,
    )

    sensors = external_repo.get_external_sensors()

    assert len(sensors) == 2

    assert external_repo.has_external_sensor("normal_sensor")

    automation_policy_sensors = [
        sensor for sensor in sensors if sensor.sensor_type == SensorType.AUTOMATION_POLICY
    ]
    assert len(automation_policy_sensors) == 1

    automation_policy_sensor = automation_policy_sensors[0]

    assert automation_policy_sensor.name == "default_automation_policy_sensor"
    assert external_repo.has_external_sensor(automation_policy_sensor.name)

    asset_graph = ExternalAssetGraph.from_external_repository(external_repo)

    assert automation_policy_sensor.asset_selection.resolve(asset_graph) == {
        AssetKey(["auto_materialize_asset"]),
        AssetKey(["auto_observe_asset"]),
        AssetKey(["other_auto_materialize_asset"]),
        AssetKey(["other_auto_observe_asset"]),
    }


def test_no_default_automation_policy_sensors(instance_without_automation_policy_sensors):
    repo_handle = MagicMock(spec=RepositoryHandle)
    repo_handle.get_external_origin.return_value = ExternalRepositoryOrigin(
        code_location_origin=RegisteredCodeLocationOrigin(location_name="foo_location"),
        repository_name="bar_repo",
    )

    # If not opted in, no default sensors are created
    external_repo = ExternalRepository(
        external_repository_data_from_def(
            defs.get_repository_def(),
        ),
        repository_handle=repo_handle,
        instance=instance_without_automation_policy_sensors,
    )
    sensors = external_repo.get_external_sensors()
    assert len(sensors) == 1
    assert sensors[0].name == "normal_sensor"


def test_combine_default_sensors_with_non_default_sensors(instance_with_automation_policy_sensors):
    automation_policy_sensor = AutomationPolicySensorDefinition(
        "my_custom_policy_sensor",
        asset_selection=[auto_materialize_asset, auto_observe_asset],
    )

    defs_with_automation_policy_sensor = Definitions(
        assets=[
            auto_materialize_asset,
            other_auto_materialize_asset,
            auto_observe_asset,
            other_auto_observe_asset,
            boring_asset,
            boring_observable_asset,
        ],
        sensors=[normal_sensor, automation_policy_sensor],
    )

    repo_handle = MagicMock(spec=RepositoryHandle)
    repo_handle.get_external_origin.return_value = ExternalRepositoryOrigin(
        code_location_origin=RegisteredCodeLocationOrigin(location_name="foo_location"),
        repository_name="bar_repo",
    )

    external_repo = ExternalRepository(
        external_repository_data_from_def(
            defs_with_automation_policy_sensor.get_repository_def(),
        ),
        repository_handle=repo_handle,
        instance=instance_with_automation_policy_sensors,
    )

    sensors = external_repo.get_external_sensors()

    assert len(sensors) == 3

    assert external_repo.has_external_sensor("normal_sensor")
    assert external_repo.has_external_sensor("default_automation_policy_sensor")
    assert external_repo.has_external_sensor("my_custom_policy_sensor")

    asset_graph = ExternalAssetGraph.from_external_repository(external_repo)

    # default sensor includes the assets that weren't covered by the custom one

    default_sensor = external_repo.get_external_sensor("default_automation_policy_sensor")

    assert default_sensor.asset_selection.resolve(asset_graph) == {
        AssetKey(["other_auto_materialize_asset"]),
        AssetKey(["other_auto_observe_asset"]),
    }

    custom_sensor = external_repo.get_external_sensor("my_custom_policy_sensor")

    assert custom_sensor.asset_selection.resolve(asset_graph) == {
        AssetKey(["auto_materialize_asset"]),
        AssetKey(["auto_observe_asset"]),
    }


def test_custom_sensors_cover_all(instance_with_automation_policy_sensors):
    automation_policy_sensor = AutomationPolicySensorDefinition(
        "my_custom_policy_sensor",
        asset_selection=[
            auto_materialize_asset,
            auto_observe_asset,
            other_auto_materialize_asset,
            other_auto_observe_asset,
        ],
    )

    defs_with_automation_policy_sensor = Definitions(
        assets=[
            auto_materialize_asset,
            other_auto_materialize_asset,
            auto_observe_asset,
            other_auto_observe_asset,
            boring_asset,
            boring_observable_asset,
        ],
        sensors=[normal_sensor, automation_policy_sensor],
    )

    repo_handle = MagicMock(spec=RepositoryHandle)
    repo_handle.get_external_origin.return_value = ExternalRepositoryOrigin(
        code_location_origin=RegisteredCodeLocationOrigin(location_name="foo_location"),
        repository_name="bar_repo",
    )

    external_repo = ExternalRepository(
        external_repository_data_from_def(
            defs_with_automation_policy_sensor.get_repository_def(),
        ),
        repository_handle=repo_handle,
        instance=instance_with_automation_policy_sensors,
    )

    sensors = external_repo.get_external_sensors()

    assert len(sensors) == 2

    assert external_repo.has_external_sensor("normal_sensor")
    assert external_repo.has_external_sensor("my_custom_policy_sensor")

    asset_graph = ExternalAssetGraph.from_external_repository(external_repo)

    # Custom sensor covered all the valid assets
    custom_sensor = external_repo.get_external_sensor("my_custom_policy_sensor")

    assert custom_sensor.asset_selection.resolve(asset_graph) == {
        AssetKey(["auto_materialize_asset"]),
        AssetKey(["auto_observe_asset"]),
        AssetKey(["other_auto_materialize_asset"]),
        AssetKey(["other_auto_observe_asset"]),
    }
