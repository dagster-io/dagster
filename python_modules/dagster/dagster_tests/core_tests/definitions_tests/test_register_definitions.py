import sys

import pytest

from dagster import (
    AssetKey,
    AssetsDefinition,
    ResourceDefinition,
    ScheduleDefinition,
    SourceAsset,
    asset,
    define_asset_job,
    op,
    register_definitions,
    repository,
    sensor,
)
from dagster._core.definitions.cacheable_assets import (
    AssetsDefinitionCacheableData,
    CacheableAssetsDefinition,
)
from dagster._core.definitions.register_definitions import (
    MAGIC_REGISTERED_DEFINITIONS_KEY,
    ModuleHasRegisteredDefinitionsError,
    get_module_name_of_registered_definitions_caller,
    get_registered_repository_in_module,
    register_definitions_test_scope,
)
from dagster._core.definitions.repository_definition import (
    PendingRepositoryDefinition,
    RepositoryDefinition,
)


def test_include_register_definition_works():
    assert register_definitions


def test_module_name_of_caller():

    # register_definitions is experimental and mark with a decorator
    # we have to add another level to the stack in order to replicate
    # the structure for a test case

    def invoke_get_module_name_of_registered_definitions_caller():
        return add_stack_frame_to_mimic_experimental()

    def add_stack_frame_to_mimic_experimental():
        return get_module_name_of_registered_definitions_caller()

    test_module_name = invoke_get_module_name_of_registered_definitions_caller()
    assert (
        test_module_name == "dagster_tests.core_tests.definitions_tests.test_register_definitions"
    )


def test_register_definitions_magic_global():
    register_definitions()
    assert MAGIC_REGISTERED_DEFINITIONS_KEY in sys.modules[__name__].__dict__
    # clean up so subsequent test cases work
    del sys.modules[__name__].__dict__[MAGIC_REGISTERED_DEFINITIONS_KEY]
    assert MAGIC_REGISTERED_DEFINITIONS_KEY not in sys.modules[__name__].__dict__


def test_register_definitions_test_scope():
    assert MAGIC_REGISTERED_DEFINITIONS_KEY not in sys.modules[__name__].__dict__
    with register_definitions_test_scope(__name__):
        register_definitions()
        assert MAGIC_REGISTERED_DEFINITIONS_KEY in sys.modules[__name__].__dict__

    assert MAGIC_REGISTERED_DEFINITIONS_KEY not in sys.modules[__name__].__dict__

    with pytest.raises(Exception, match="test cleanup"):
        with register_definitions_test_scope(__name__):
            register_definitions()
            raise Exception("test cleanup")

    assert MAGIC_REGISTERED_DEFINITIONS_KEY not in sys.modules[__name__].__dict__


def test_register_definitions_called_twice():
    with register_definitions_test_scope(__name__):
        register_definitions()
        with pytest.raises(ModuleHasRegisteredDefinitionsError):
            register_definitions()


def get_all_assets_from_repo(repo):
    # could not find public method on repository to do this
    return list(repo._assets_defs_by_key.values())  # pylint: disable=protected-access


def get_resolved_repository_in_scope() -> RepositoryDefinition:
    repo_or_caching_repo = get_registered_repository_in_module(__name__)
    return (
        repo_or_caching_repo.compute_repository_definition()
        if isinstance(repo_or_caching_repo, PendingRepositoryDefinition)
        else repo_or_caching_repo
    )


def test_basic_asset_definitions():
    with register_definitions_test_scope(__name__):

        @asset
        def an_asset():
            pass

        register_definitions(assets=[an_asset])

        repo = get_resolved_repository_in_scope()
        all_assets = get_all_assets_from_repo(repo)
        assert len(all_assets) == 1
        assert all_assets[0].key.to_user_string() == "an_asset"


def test_basic_schedule_definition():
    with register_definitions_test_scope(__name__):

        @asset
        def an_asset():
            pass

        register_definitions(
            assets=[an_asset],
            schedules=[
                ScheduleDefinition(
                    name="daily_an_asset_schedule",
                    job=define_asset_job(name="an_asset_job"),
                    cron_schedule="@daily",
                )
            ],
        )

        repo = get_resolved_repository_in_scope()
        assert repo.get_schedule_def("daily_an_asset_schedule")


def test_basic_sensor_definition():
    with register_definitions_test_scope(__name__):

        @asset
        def an_asset():
            pass

        an_asset_job = define_asset_job(name="an_asset_job")

        @sensor(name="an_asset_sensor", job=an_asset_job)
        def a_sensor():
            raise NotImplementedError()

        register_definitions(
            assets=[an_asset],
            sensors=[a_sensor],
        )

        repo = get_resolved_repository_in_scope()

        assert repo.get_sensor_def("an_asset_sensor")


def test_with_resource_binding():
    with register_definitions_test_scope(__name__):

        executed = {}

        @asset(required_resource_keys={"foo"})
        def requires_foo(context):
            assert context.resources.foo == "wrapped"
            executed["yes"] = True

        register_definitions(
            assets=[requires_foo],
            resources={"foo": ResourceDefinition.hardcoded_resource("wrapped")},
        )

        repo = get_resolved_repository_in_scope()

        asset_job = repo.get_all_jobs()[0]
        asset_job.execute_in_process()
        assert executed["yes"]


def test_resource_coercion():
    with register_definitions_test_scope(__name__):

        executed = {}

        @asset(required_resource_keys={"foo"})
        def requires_foo(context):
            assert context.resources.foo == "object-to-coerce"
            executed["yes"] = True

        register_definitions(
            assets=[requires_foo],
            resources={"foo": "object-to-coerce"},
        )

        repo = get_resolved_repository_in_scope()

        asset_job = repo.get_all_jobs()[0]
        asset_job.execute_in_process()
        assert executed["yes"]


def test_source_asset():
    with register_definitions_test_scope(__name__):
        register_definitions(assets=[SourceAsset("a-source-asset")])

        repo = get_resolved_repository_in_scope()
        all_assets = list(repo.source_assets_by_key.values())
        assert len(all_assets) == 1
        assert all_assets[0].key.to_user_string() == "a-source-asset"


def test_pending_definitions():
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

    with register_definitions_test_scope(__name__):
        register_definitions(assets=[MyCacheableAssetsDefinition("foobar")])
        repo = get_resolved_repository_in_scope()
        all_assets = get_all_assets_from_repo(repo)
        assert len(all_assets) == 1
        assert all_assets[0].key.to_user_string() == "foobar"
