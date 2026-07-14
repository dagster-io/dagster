import dagster as dg
import pytest
from dagster import AutoMaterializePolicy
from dagster._core.definitions.asset_key import AssetJobKey
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.assets.graph.asset_graph import AssetGraph
from dagster._core.definitions.sensor_definition import SensorType
from dagster._core.remote_representation.external import RemoteRepository
from dagster._core.remote_representation.external_data import RepositorySnap
from dagster._core.remote_representation.handle import RepositoryHandle


@dg.asset(auto_materialize_policy=AutoMaterializePolicy.eager())
def auto_materialize_asset():
    pass


@dg.asset(auto_materialize_policy=AutoMaterializePolicy.eager())
def other_auto_materialize_asset():
    pass


auto_observe_asset = dg.SourceAsset(
    key="auto_observe_asset",
    observe_fn=lambda context: dg.DataVersion("1"),
    auto_observe_interval_minutes=1,
)

other_auto_observe_asset = dg.SourceAsset(
    key="other_auto_observe_asset",
    observe_fn=lambda context: dg.DataVersion("1"),
    auto_observe_interval_minutes=1,
)


@dg.asset
def boring_asset():
    pass


@dg.observable_source_asset
def boring_observable_asset():
    pass


@dg.sensor(asset_selection=[auto_materialize_asset])
def normal_sensor():
    yield dg.SkipReason("OOPS")


defs = dg.Definitions(
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

defs_without_observables = dg.Definitions(
    assets=[
        auto_materialize_asset,
        other_auto_materialize_asset,
        boring_asset,
    ],
)


@pytest.fixture
def instance_with_auto_materialize_sensors():
    with dg.instance_for_test() as the_instance:
        yield the_instance


@pytest.fixture
def instance_without_auto_materialize_sensors():
    with dg.instance_for_test({"auto_materialize": {"use_sensors": False}}) as the_instance:
        yield the_instance


def test_default_auto_materialize_sensors():
    repo_handle = RepositoryHandle.for_test(
        location_name="foo_location",
        repository_name="bar_repo",
    )
    remote_repo = RemoteRepository(
        RepositorySnap.from_def(
            defs.get_repository_def(),
        ),
        repository_handle=repo_handle,
        auto_materialize_use_sensors=True,
    )

    sensors = remote_repo.get_sensors()

    assert len(sensors) == 2

    assert remote_repo.has_sensor("normal_sensor")

    auto_materialize_sensors = [s for s in sensors if s.sensor_type == SensorType.AUTO_MATERIALIZE]
    assert len(auto_materialize_sensors) == 1

    auto_materialize_sensor = auto_materialize_sensors[0]

    assert auto_materialize_sensor.name == "default_automation_condition_sensor"
    assert remote_repo.has_sensor(auto_materialize_sensor.name)

    assert auto_materialize_sensor.asset_selection == AssetSelection.all(include_sources=True)


def test_default_auto_materialize_sensors_without_observable():
    repo_handle = RepositoryHandle.for_test(
        location_name="foo_location",
        repository_name="bar_repo",
    )

    remote_repo = RemoteRepository(
        RepositorySnap.from_def(
            defs_without_observables.get_repository_def(),
        ),
        repository_handle=repo_handle,
        auto_materialize_use_sensors=True,
    )

    sensors = remote_repo.get_sensors()

    assert len(sensors) == 1

    auto_materialize_sensor = sensors[0]

    assert auto_materialize_sensor.name == "default_automation_condition_sensor"
    assert remote_repo.has_sensor(auto_materialize_sensor.name)

    assert auto_materialize_sensor.asset_selection == AssetSelection.all(include_sources=False)


def test_opt_out_default_auto_materialize_sensors():
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
        auto_materialize_use_sensors=True,
    )
    sensors = remote_repo.get_sensors()
    assert len(sensors) == 2
    assert sensors[0].name == "default_automation_condition_sensor"
    assert sensors[1].name == "normal_sensor"


def test_combine_default_sensors_with_non_default_sensors():
    auto_materialize_sensor = dg.AutomationConditionSensorDefinition(
        "my_custom_policy_sensor",
        target=[auto_materialize_asset, auto_observe_asset],
    )

    defs_with_auto_materialize_sensor = dg.Definitions(
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
        auto_materialize_use_sensors=True,
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
        == 'not key:"auto_materialize_asset" or key:"auto_observe_asset"'
    )

    assert default_sensor.asset_selection.resolve(asset_graph) == {  # ty: ignore[unresolved-attribute]
        dg.AssetKey(["other_auto_materialize_asset"]),
        dg.AssetKey(["other_auto_observe_asset"]),
        dg.AssetKey(["boring_asset"]),
        dg.AssetKey(["boring_observable_asset"]),
    }

    custom_sensor = remote_repo.get_sensor("my_custom_policy_sensor")

    assert custom_sensor.asset_selection.resolve(asset_graph) == {  # ty: ignore[unresolved-attribute]
        dg.AssetKey(["auto_materialize_asset"]),
        dg.AssetKey(["auto_observe_asset"]),
    }


def test_custom_sensors_cover_all():
    auto_materialize_sensor = dg.AutomationConditionSensorDefinition(
        "my_custom_policy_sensor",
        target=[
            auto_materialize_asset,
            auto_observe_asset,
            other_auto_materialize_asset,
            other_auto_observe_asset,
        ],
    )

    defs_with_auto_materialize_sensor = dg.Definitions(
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
        auto_materialize_use_sensors=True,
    )

    sensors = remote_repo.get_sensors()

    assert len(sensors) == 2

    assert remote_repo.has_sensor("normal_sensor")
    assert remote_repo.has_sensor("my_custom_policy_sensor")

    asset_graph = remote_repo.asset_graph

    # Custom sensor covered all the valid assets
    custom_sensor = remote_repo.get_sensor("my_custom_policy_sensor")

    assert custom_sensor.asset_selection.resolve(asset_graph) == {  # ty: ignore[unresolved-attribute]
        dg.AssetKey(["auto_materialize_asset"]),
        dg.AssetKey(["auto_observe_asset"]),
        dg.AssetKey(["other_auto_materialize_asset"]),
        dg.AssetKey(["other_auto_observe_asset"]),
    }


def _local_sensor_names(defs: dg.Definitions) -> set[str]:
    return {s.name for s in defs.get_repository_def().sensor_defs}


def _remote_sensor_names(defs: dg.Definitions) -> set[str]:
    remote_repo = RemoteRepository(
        RepositorySnap.from_def(defs.get_repository_def()),
        repository_handle=RepositoryHandle.for_test(
            location_name="foo_location", repository_name="bar_repo"
        ),
        auto_materialize_use_sensors=True,
    )
    return {s.name for s in remote_repo.get_sensors()}


def _unresolved_conditioned_job(asset, automation_condition):
    # arrives via define_asset_job; lands in the builder's `unresolved_jobs`
    return dg.define_asset_job(
        name="the_job", selection=[asset], automation_condition=automation_condition
    )


def _resolved_conditioned_job(asset, automation_condition):
    # an already-resolved asset job (e.g. via .resolve()) passed directly into Definitions;
    # lands in the builder's `jobs` dict rather than `unresolved_jobs`
    return dg.define_asset_job(
        name="the_job", selection=[asset], automation_condition=automation_condition
    ).resolve(asset_graph=AssetGraph.from_assets([asset]))


# local: the sensor is added during Definitions construction (repository_data_builder,
# which passes conditioned-job names explicitly). remote: it is computed from the remote
# graph's own job nodes (external.py), exercising automatable_asset_job_keys.
@pytest.mark.parametrize(
    "sensor_names_from_defs", [_local_sensor_names, _remote_sensor_names], ids=["local", "remote"]
)
# a conditioned job reaches the builder either unresolved (define_asset_job) or already
# resolved (JobDefinition passed directly); both must summon the default sensor.
@pytest.mark.parametrize(
    "job_factory",
    [_unresolved_conditioned_job, _resolved_conditioned_job],
    ids=["unresolved", "resolved"],
)
@pytest.mark.parametrize(
    "automation_condition,expect_default_sensor",
    [(dg.AutomationCondition.eager(), True), (None, False)],
    ids=["conditioned_job", "unconditioned_job"],
)
def test_default_sensor_for_automation_conditioned_job(
    sensor_names_from_defs,
    job_factory,
    automation_condition,
    expect_default_sensor: bool,
) -> None:
    """A job's automation condition alone (no conditioned assets or checks anywhere)
    must decide whether the default automation condition sensor is created.
    """

    @dg.asset
    def plain_asset():
        return 1

    job = job_factory(plain_asset, automation_condition)
    defs = dg.Definitions(assets=[plain_asset], jobs=[job])

    sensor_names = sensor_names_from_defs(defs)
    assert ("default_automation_condition_sensor" in sensor_names) == expect_default_sensor


def test_conditioned_jobs_collected_from_both_unresolved_and_resolved() -> None:
    """The builder must collect conditioned jobs from BOTH sources at once: unresolved
    (define_asset_job) and already-resolved (JobDefinition passed directly).
    """

    @dg.asset
    def asset_a():
        return 1

    @dg.asset
    def asset_b():
        return 1

    unresolved_job = dg.define_asset_job(
        name="unresolved_job",
        selection=[asset_a],
        automation_condition=dg.AutomationCondition.eager(),
    )
    resolved_job = dg.define_asset_job(
        name="resolved_job",
        selection=[asset_b],
        automation_condition=dg.AutomationCondition.eager(),
    ).resolve(asset_graph=AssetGraph.from_assets([asset_b]))

    defs = dg.Definitions(assets=[asset_a, asset_b], jobs=[unresolved_job, resolved_job])

    asset_graph = defs.get_repository_def().asset_graph
    assert asset_graph.automatable_asset_job_keys == {
        AssetJobKey("unresolved_job"),
        AssetJobKey("resolved_job"),
    }
