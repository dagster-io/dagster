import sys

import pytest

from dagster import (
    ResourceDefinition,
    ScheduleDefinition,
    asset,
    define_asset_job,
    definitions,
    job,
    op,
    sensor,
)
from dagster._core.definitions.definitions_fn import (
    MAGIC_REPO_GLOBAL_KEY,
    DefinitionsAlreadyCalledError,
    definitions_test_scope,
    get_python_env_global_dagster_repository,
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


def test_contextmanager_test_helper():
    assert MAGIC_REPO_GLOBAL_KEY not in sys.modules[__name__].__dict__
    with definitions_test_scope(__name__):
        sys.modules[__name__].__dict__[MAGIC_REPO_GLOBAL_KEY] = "test"

    assert MAGIC_REPO_GLOBAL_KEY not in sys.modules[__name__].__dict__

    try:
        with definitions_test_scope(__name__):
            sys.modules[__name__].__dict__[MAGIC_REPO_GLOBAL_KEY] = "test"
            raise Exception("foobar")
    except Exception:
        pass

    assert MAGIC_REPO_GLOBAL_KEY not in sys.modules[__name__].__dict__


def test_basic_asset_definitions():
    with definitions_test_scope(__name__):

        @asset
        def an_asset():
            pass

        definitions(assets=[an_asset])

        repo = get_python_env_global_dagster_repository()
        all_assets = list(repo._assets_defs_by_key.values())  # pylint: disable=protected-access)
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

        repo = get_python_env_global_dagster_repository()

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

        repo = get_python_env_global_dagster_repository()
        assert repo.get_schedule_def("daily_an_asset_schedule")


def test_basic_sensor_definition():
    with definitions_test_scope(__name__):

        @asset
        def an_asset():
            pass

        an_asset_job = define_asset_job(name="an_asset_job")

        @sensor(name="an_asset_sensor", job=an_asset_job)
        def a_sensor():
            pass

        definitions(
            assets=[an_asset],
            sensors=[a_sensor],
        )

        repo = get_python_env_global_dagster_repository()

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

        repo = get_python_env_global_dagster_repository()

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

        repo = get_python_env_global_dagster_repository()

        asset_job = repo.get_all_jobs()[0]
        asset_job.execute_in_process()

        assert executed["yes"]
