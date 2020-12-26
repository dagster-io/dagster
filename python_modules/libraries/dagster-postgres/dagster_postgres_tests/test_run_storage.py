import pytest
import yaml
from dagster.core.events import DagsterEvent, DagsterEventType
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus, PipelineRunsFilter
from dagster.core.test_utils import environ, instance_for_test
from dagster.core.utils import make_new_run_id
from dagster_tests.core_tests.storage_tests.utils.run_storage import TestRunStorage


class TestPostgresRunStorage(TestRunStorage):
    __test__ = True

    @pytest.fixture(scope="function", name="storage")
    def run_storage(self, clean_storage):  # pylint: disable=arguments-differ
        return clean_storage


def build_run(
    run_id, pipeline_name, mode="default", tags=None, status=PipelineRunStatus.NOT_STARTED
):
    return PipelineRun(
        pipeline_name=pipeline_name,
        run_id=run_id,
        run_config=None,
        mode=mode,
        step_keys_to_execute=None,
        tags=tags,
        status=status,
    )


def test_add_get_postgres_run_storage(clean_storage):
    run_storage = clean_storage
    run_id = make_new_run_id()
    run_to_add = build_run(pipeline_name="pipeline_name", run_id=run_id)
    added = run_storage.add_run(run_to_add)
    assert added

    fetched_run = run_storage.get_run_by_id(run_id)

    assert run_to_add == fetched_run

    assert run_storage.has_run(run_id)
    assert not run_storage.has_run(make_new_run_id())

    assert run_storage.get_runs() == [run_to_add]
    assert run_storage.get_runs(PipelineRunsFilter(pipeline_name="pipeline_name")) == [run_to_add]
    assert run_storage.get_runs(PipelineRunsFilter(pipeline_name="nope")) == []

    run_storage.wipe()
    assert run_storage.get_runs() == []


def test_handle_run_event_pipeline_success_test(clean_storage):
    run_storage = clean_storage

    run_id = make_new_run_id()
    run_to_add = build_run(pipeline_name="pipeline_name", run_id=run_id)
    run_storage.add_run(run_to_add)

    dagster_pipeline_start_event = DagsterEvent(
        message="a message",
        event_type_value=DagsterEventType.PIPELINE_START.value,
        pipeline_name="pipeline_name",
        step_key=None,
        solid_handle=None,
        step_kind_value=None,
        logging_tags=None,
    )

    run_storage.handle_run_event(run_id, dagster_pipeline_start_event)

    assert run_storage.get_run_by_id(run_id).status == PipelineRunStatus.STARTED

    run_storage.handle_run_event(
        make_new_run_id(),  # diff run
        DagsterEvent(
            message="a message",
            event_type_value=DagsterEventType.PIPELINE_SUCCESS.value,
            pipeline_name="pipeline_name",
            step_key=None,
            solid_handle=None,
            step_kind_value=None,
            logging_tags=None,
        ),
    )

    assert run_storage.get_run_by_id(run_id).status == PipelineRunStatus.STARTED

    run_storage.handle_run_event(
        run_id,  # correct run
        DagsterEvent(
            message="a message",
            event_type_value=DagsterEventType.PIPELINE_SUCCESS.value,
            pipeline_name="pipeline_name",
            step_key=None,
            solid_handle=None,
            step_kind_value=None,
            logging_tags=None,
        ),
    )

    assert run_storage.get_run_by_id(run_id).status == PipelineRunStatus.SUCCESS


def test_load_from_config(hostname):
    url_cfg = """
      run_storage:
        module: dagster_postgres.run_storage
        class: PostgresRunStorage
        config:
          postgres_url: postgresql://test:test@{hostname}:5432/test
    """.format(
        hostname=hostname
    )

    explicit_cfg = """
      run_storage:
        module: dagster_postgres.run_storage
        class: PostgresRunStorage
        config:
          postgres_db:
            username: test
            password: test
            hostname: {hostname}
            db_name: test
    """.format(
        hostname=hostname
    )

    with environ({"TEST_PG_PASSWORD": "test"}):
        env_cfg = """
        run_storage:
          module: dagster_postgres.run_storage
          class: PostgresRunStorage
          config:
            postgres_db:
              username: test
              password:
                env: TEST_PG_PASSWORD
              hostname: {hostname}
              db_name: test
        """.format(
            hostname=hostname
        )

        # pylint: disable=protected-access
        with instance_for_test(overrides=yaml.safe_load(url_cfg)) as from_url_instance:
            with instance_for_test(
                overrides=yaml.safe_load(explicit_cfg)
            ) as from_explicit_instance:
                assert (
                    from_url_instance._run_storage.postgres_url
                    == from_explicit_instance._run_storage.postgres_url
                )
            with instance_for_test(overrides=yaml.safe_load(env_cfg)) as from_env_instance:
                assert (
                    from_url_instance._run_storage.postgres_url
                    == from_env_instance._run_storage.postgres_url
                )
