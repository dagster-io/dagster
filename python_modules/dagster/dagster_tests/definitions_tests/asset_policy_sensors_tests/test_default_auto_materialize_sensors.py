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
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.automation_condition_sensor_definition import (
    AutomationConditionSensorDefinition,
)
from dagster._core.definitions.sensor_definition import SensorType
from dagster._core.remote_representation.external import RemoteRepository
from dagster._core.remote_representation.external_data import RepositorySnap
from dagster._core.remote_representation.handle import RepositoryHandle
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


@sensor(asset_selection=[auto_materialize_asset])
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

defs_without_observables = Definitions(
    assets=[
        auto_materialize_asset,
        other_auto_materialize_asset,
        boring_asset,
    ],
)


@pytest.fixture
def instance_with_auto_materialize_sensors():
    with instance_for_test() as the_instance:
        yield the_instance


@pytest.fixture
def instance_without_auto_materialize_sensors():
    with instance_for_test({"auto_materialize": {"use_sensors": False}}) as the_instance:
        yield the_instance


def test_default_auto_materialize_sensors(instance_with_auto_materialize_sensors):
    instance = instance_with_auto_materialize_sensors
    repo_handle = RepositoryHandle.for_test(
        location_name="foo_location",
        repository_name="bar_repo",
    )
    remote_repo = RemoteRepository(
        RepositorySnap.from_def(
            defs.get_repository_def(),
        ),
        repository_handle=repo_handle,
        instance=instance,
    )

    sensors = remote_repo.get_sensors()

    assert len(sensors) == 2

    assert remote_repo.has_sensor("normal_sensor")

    auto_materialize_sensors = [
        sensor for sensor in sensors if sensor.sensor_type == SensorType.AUTO_MATERIALIZE
    ]
    assert len(auto_materialize_sensors) == 1

    auto_materialize_sensor = auto_materialize_sensors[0]

    assert auto_materialize_sensor.name == "default_automation_condition_sensor"
    assert remote_repo.has_sensor(auto_materialize_sensor.name)

    assert auto_materialize_sensor.asset_selection == AssetSelection.all(include_sources=True)


def test_default_auto_materialize_sensors_without_observable(
    instance_with_auto_materialize_sensors,
):
    instance = instance_with_auto_materialize_sensors

    repo_handle = RepositoryHandle.for_test(
        location_name="foo_location",
        repository_name="bar_repo",
    )

    remote_repo = RemoteRepository(
        RepositorySnap.from_def(
            defs_without_observables.get_repository_def(),
        ),
        repository_handle=repo_handle,
        instance=instance,
    )

    sensors = remote_repo.get_sensors()

    assert len(sensors) == 1

    auto_materialize_sensor = sensors[0]

    assert auto_materialize_sensor.name == "default_automation_condition_sensor"
    assert remote_repo.has_sensor(auto_materialize_sensor.name)

    assert auto_materialize_sensor.asset_selection == AssetSelection.all(include_sources=False)


def test_opt_out_default_auto_materialize_sensors(instance_without_auto_materialize_sensors):
    repo_handle = RepositoryHandle.for_test(
        location_name="foo_location",
        repository_name="bar_repo",
    )

    # If opted out, we still do create default auto materialize sensors
    remote_repo = RemoteRepository(
        RepositorySnap.from_def(
            defs.get_repository_def(),
        ),
        repository_handle=repo_handle,
        instance=instance_without_auto_materialize_sensors,
    )
    sensors = remote_repo.get_sensors()
    assert len(sensors) == 2
    assert sensors[0].name == "default_automation_condition_sensor"
    assert sensors[1].name == "normal_sensor"


def test_combine_default_sensors_with_non_default_sensors(instance_with_auto_materialize_sensors):
    auto_materialize_sensor = AutomationConditionSensorDefinition(
        "my_custom_policy_sensor",
        asset_selection=[auto_materialize_asset, auto_observe_asset],
    )

    defs_with_auto_materialize_sensor = Definitions(
        assets=[
            auto_materialize_asset,
            other_auto_materialize_asset,
            auto_observe_asset,
            other_auto_observe_asset,
            boring_asset,
            boring_observable_asset,
        ],
        sensors=[normal_sensor, auto_materialize_sensor],
    )
    repo_handle = RepositoryHandle.for_test(
        location_name="foo_location",
        repository_name="bar_repo",
    )

    remote_repo = RemoteRepository(
        RepositorySnap.from_def(
            defs_with_auto_materialize_sensor.get_repository_def(),
        ),
        repository_handle=repo_handle,
        instance=instance_with_auto_materialize_sensors,
    )

    sensors = remote_repo.get_sensors()

    assert len(sensors) == 3

    assert remote_repo.has_sensor("normal_sensor")
    assert remote_repo.has_sensor("default_automation_condition_sensor")
    assert remote_repo.has_sensor("my_custom_policy_sensor")

    asset_graph = remote_repo.asset_graph

    # default sensor includes all assets that weren't covered by the custom one

    default_sensor = remote_repo.get_sensor("default_automation_condition_sensor")

    assert (
        str(default_sensor.asset_selection)
        == "all materializable assets and source assets - (auto_materialize_asset or auto_observe_asset)"
    )

    assert default_sensor.asset_selection.resolve(asset_graph) == {
        AssetKey(["other_auto_materialize_asset"]),
        AssetKey(["other_auto_observe_asset"]),
        AssetKey(["boring_asset"]),
        AssetKey(["boring_observable_asset"]),
    }

    custom_sensor = remote_repo.get_sensor("my_custom_policy_sensor")

    assert custom_sensor.asset_selection.resolve(asset_graph) == {
        AssetKey(["auto_materialize_asset"]),
        AssetKey(["auto_observe_asset"]),
    }


def test_custom_sensors_cover_all(instance_with_auto_materialize_sensors):
    auto_materialize_sensor = AutomationConditionSensorDefinition(
        "my_custom_policy_sensor",
        asset_selection=[
            auto_materialize_asset,
            auto_observe_asset,
            other_auto_materialize_asset,
            other_auto_observe_asset,
        ],
    )

    defs_with_auto_materialize_sensor = Definitions(
        assets=[
            auto_materialize_asset,
            other_auto_materialize_asset,
            auto_observe_asset,
            other_auto_observe_asset,
            boring_asset,
            boring_observable_asset,
        ],
        sensors=[normal_sensor, auto_materialize_sensor],
    )

    repo_handle = RepositoryHandle.for_test(
        location_name="foo_location",
        repository_name="bar_repo",
    )

    remote_repo = RemoteRepository(
        RepositorySnap.from_def(
            defs_with_auto_materialize_sensor.get_repository_def(),
        ),
        repository_handle=repo_handle,
        instance=instance_with_auto_materialize_sensors,
    )

    sensors = remote_repo.get_sensors()

    assert len(sensors) == 2

    assert remote_repo.has_sensor("normal_sensor")
    assert remote_repo.has_sensor("my_custom_policy_sensor")

    asset_graph = remote_repo.asset_graph

    # Custom sensor covered all the valid assets
    custom_sensor = remote_repo.get_sensor("my_custom_policy_sensor")

    assert custom_sensor.asset_selection.resolve(asset_graph) == {
        AssetKey(["auto_materialize_asset"]),
        AssetKey(["auto_observe_asset"]),
        AssetKey(["other_auto_materialize_asset"]),
        AssetKey(["other_auto_observe_asset"]),
    }
