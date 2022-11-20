from dagster import (
    AssetKey,
    AssetsDefinition,
    Definitions,
    ResourceDefinition,
    ScheduleDefinition,
    SourceAsset,
    asset,
    define_asset_job,
    op,
    repository,
    sensor,
)
from dagster._core.definitions.cacheable_assets import (
    AssetsDefinitionCacheableData,
    CacheableAssetsDefinition,
)
from dagster._core.definitions.repository_definition import (
    PendingRepositoryDefinition,
    RepositoryDefinition,
)


def get_all_assets_from_defs(defs: Definitions):
    # could not find public method on repository to do this
    repo = resolve_pending_repo_if_required(defs)
    return list(repo._assets_defs_by_key.values())  # pylint: disable=protected-access


# TODO: introduce common interface to avoid this coercion
def resolve_pending_repo_if_required(definitions: Definitions) -> RepositoryDefinition:
    repo_or_caching_repo = definitions.get_inner_repository()
    return (
        repo_or_caching_repo.compute_repository_definition()
        if isinstance(repo_or_caching_repo, PendingRepositoryDefinition)
        else repo_or_caching_repo
    )


def test_basic_asset():
    assert Definitions

    @asset
    def an_asset():
        pass

    defs = Definitions(assets=[an_asset])

    all_assets = get_all_assets_from_defs(defs)
    assert len(all_assets) == 1
    assert all_assets[0].key.to_user_string() == "an_asset"


def test_basic_schedule_definition():
    @asset
    def an_asset():
        pass

    defs = Definitions(
        assets=[an_asset],
        schedules=[
            ScheduleDefinition(
                name="daily_an_asset_schedule",
                job=define_asset_job(name="an_asset_job"),
                cron_schedule="@daily",
            )
        ],
    )

    assert resolve_pending_repo_if_required(defs).get_schedule_def("daily_an_asset_schedule")


def test_basic_sensor_definition():
    @asset
    def an_asset():
        pass

    an_asset_job = define_asset_job(name="an_asset_job")

    @sensor(name="an_asset_sensor", job=an_asset_job)
    def a_sensor():
        raise NotImplementedError()

    defs = Definitions(
        assets=[an_asset],
        sensors=[a_sensor],
    )
    repo = resolve_pending_repo_if_required(defs)

    assert repo.get_sensor_def("an_asset_sensor")


def test_with_resource_binding():
    executed = {}

    @asset(required_resource_keys={"foo"})
    def requires_foo(context):
        assert context.resources.foo == "wrapped"
        executed["yes"] = True

    defs = Definitions(
        assets=[requires_foo],
        resources={"foo": ResourceDefinition.hardcoded_resource("wrapped")},
    )
    repo = resolve_pending_repo_if_required(defs)
    asset_job = repo.get_all_jobs()[0]
    asset_job.execute_in_process()
    assert executed["yes"]


def test_resource_coercion():
    executed = {}

    @asset(required_resource_keys={"foo"})
    def requires_foo(context):
        assert context.resources.foo == "object-to-coerce"
        executed["yes"] = True

    defs = Definitions(
        assets=[requires_foo],
        resources={"foo": "object-to-coerce"},
    )
    repo = resolve_pending_repo_if_required(defs)
    asset_job = repo.get_all_jobs()[0]
    asset_job.execute_in_process()
    assert executed["yes"]


def test_source_asset():
    defs = Definitions(assets=[SourceAsset("a-source-asset")])
    repo = resolve_pending_repo_if_required(defs)
    all_assets = list(repo.source_assets_by_key.values())
    assert len(all_assets) == 1
    assert all_assets[0].key.to_user_string() == "a-source-asset"


def test_pending_repo():
    class MyCacheableAssetsDefinition(CacheableAssetsDefinition):
        def compute_cacheable_data(self):
            return [
                AssetsDefinitionCacheableData(
                    keys_by_input_name={}, keys_by_output_name={"result": AssetKey(self.unique_id)}
                )
            ]

        def build_definitions(self, data):
            @op
            def my_op():
                return 1

            return [
                AssetsDefinition.from_op(
                    my_op,
                    keys_by_input_name=cd.keys_by_input_name,
                    keys_by_output_name=cd.keys_by_output_name,
                )
                for cd in data
            ]

    # This section of the test was just to test my understanding of what is happening
    # here and then it also documents why resolve_pending_repo_if_required is necessary
    @repository
    def a_pending_repo():
        return [MyCacheableAssetsDefinition("foobar")]

    assert isinstance(a_pending_repo, PendingRepositoryDefinition)
    assert isinstance(a_pending_repo.compute_repository_definition(), RepositoryDefinition)

    # now actually test definitions

    defs = Definitions(assets=[MyCacheableAssetsDefinition("foobar")])
    all_assets = get_all_assets_from_defs(defs)
    assert len(all_assets) == 1
    assert all_assets[0].key.to_user_string() == "foobar"
