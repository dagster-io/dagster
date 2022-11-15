import sys

import pytest

from dagster import AssetKey, AssetsDefinition, ResourceDefinition, ScheduleDefinition, SkipReason
from dagster import _check as check
from dagster import asset, define_asset_job, definitions, job, op, repository, sensor
from dagster._core.definitions.cacheable_assets import (
    AssetsDefinitionCacheableData,
    CacheableAssetsDefinition,
)
from dagster._core.definitions.definitions_fn import (
    MAGIC_REPO_GLOBAL_KEY,
    DefinitionsAlreadyCalledError,
    definitions_test_scope,
    get_dagster_repository_in_module,
)
from dagster._core.definitions.repository_definition import (
    PendingRepositoryDefinition,
    RepositoryDefinition,
)


def test_assert_definitions_fn():
    assert definitions


def test_definitions_is_magic_global_set():
    definitions()
    # automatically test and cleanup
    assert MAGIC_REPO_GLOBAL_KEY in sys.modules[__name__].__dict__
    del sys.modules[__name__].__dict__[MAGIC_REPO_GLOBAL_KEY]
    assert MAGIC_REPO_GLOBAL_KEY not in sys.modules[__name__].__dict__


def test_definitions_invoke_twice():
    with definitions_test_scope(__name__):
        definitions()
        with pytest.raises(DefinitionsAlreadyCalledError):
            definitions()


def get_defined_repo() -> RepositoryDefinition:
    repo_or_caching_repo = get_dagster_repository_in_module(__name__)
    return (
        repo_or_caching_repo.compute_repository_definition()
        if isinstance(repo_or_caching_repo, PendingRepositoryDefinition)
        else repo_or_caching_repo
    )


def test_contextmanager_test_helper():
    assert MAGIC_REPO_GLOBAL_KEY not in sys.modules[__name__].__dict__

    @repository
    def a_repo():
        return []

    with definitions_test_scope(__name__):
        sys.modules[__name__].__dict__[MAGIC_REPO_GLOBAL_KEY] = a_repo

    assert MAGIC_REPO_GLOBAL_KEY not in sys.modules[__name__].__dict__

    try:
        with definitions_test_scope(__name__):
            sys.modules[__name__].__dict__[MAGIC_REPO_GLOBAL_KEY] = a_repo
            raise Exception("foobar")
            # globals should be unset in finally block of definitions_test_scope
    except Exception:
        pass

    assert MAGIC_REPO_GLOBAL_KEY not in sys.modules[__name__].__dict__


def get_all_assets_from_repo(repo):
    # could not find public method on repository to do this
    return list(repo._assets_defs_by_key.values())  # pylint: disable=protected-access


def test_basic_asset_definitions():
    with definitions_test_scope(__name__):

        @asset
        def an_asset():
            pass

        definitions(assets=[an_asset])

        repo = get_defined_repo()
        all_assets = get_all_assets_from_repo(repo)
        # all_assets = list(repo._assets_defs_by_key.values())  # pylint: disable=protected-access
        assert len(all_assets) == 1
        assert all_assets[0].key.to_user_string() == "an_asset"


def test_basic_job_definition():
    with definitions_test_scope(__name__):

        @op
        def an_op():
            pass

        @job
        def a_job():
            an_op()

        definitions(jobs=[a_job])

        repo = get_defined_repo()

        jobs = repo.get_all_jobs()
        assert len(jobs) == 1
        assert jobs[0].name == "a_job"


def test_basic_schedule_definition():
    with definitions_test_scope(__name__):

        @asset
        def an_asset():
            pass

        definitions(
            assets=[an_asset],
            schedules=[
                ScheduleDefinition(
                    name="daily_an_asset_schedule",
                    job=define_asset_job(name="an_asset_job"),
                    cron_schedule="@daily",
                )
            ],
        )

        repo = get_defined_repo()
        assert repo.get_schedule_def("daily_an_asset_schedule")


def test_basic_sensor_definition():
    with definitions_test_scope(__name__):

        @asset
        def an_asset():
            pass

        an_asset_job = define_asset_job(name="an_asset_job")

        @sensor(name="an_asset_sensor", job=an_asset_job)
        def a_sensor():
            yield SkipReason("type check do not bother me")

        definitions(
            assets=[an_asset],
            sensors=[a_sensor],
        )

        repo = get_defined_repo()

        assert repo.get_sensor_def("an_asset_sensor")


def test_with_resource_binding():
    with definitions_test_scope(__name__):

        executed = {}

        @asset(required_resource_keys={"foo"})
        def requires_foo(context):
            assert context.resources.foo == "wrapped"
            executed["yes"] = True

        definitions(
            assets=[requires_foo],
            resources={"foo": ResourceDefinition.hardcoded_resource("wrapped")},
        )

        repo = get_defined_repo()

        asset_job = repo.get_all_jobs()[0]
        asset_job.execute_in_process()
        assert executed["yes"]


def test_with_resource_wrapping():
    with definitions_test_scope(__name__):

        executed = {}

        @asset(required_resource_keys={"foo"})
        def requires_foo(context):
            assert context.resources.foo == "raw"
            executed["yes"] = True

        definitions(
            assets=[requires_foo],
            resources={"foo": "raw"},
        )

        repo = get_defined_repo()

        asset_job = repo.get_all_jobs()[0]
        asset_job.execute_in_process()

        assert executed["yes"]


def test_global_pending_repo():
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

    @repository
    def a_pending_repo():
        return [MyCacheableAssetsDefinition("foobar")]

    assert isinstance(a_pending_repo, PendingRepositoryDefinition)

    assert isinstance(a_pending_repo.compute_repository_definition(), RepositoryDefinition)

    with definitions_test_scope(__name__):
        definitions(assets=[MyCacheableAssetsDefinition("foobar")])
        repo = get_defined_repo()
        all_assets = get_all_assets_from_repo(repo)
        assert len(all_assets) == 1
        assert all_assets[0].key.to_user_string() == "foobar"
