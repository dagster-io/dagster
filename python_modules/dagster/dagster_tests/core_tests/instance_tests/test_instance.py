import re

import pytest
import yaml
from dagster import PipelineDefinition, check, execute_pipeline, pipeline, solid
from dagster.check import CheckError
from dagster.config import Field
from dagster.core.errors import (
    DagsterHomeNotSetError,
    DagsterInvalidConfigError,
    DagsterInvariantViolationError,
)
from dagster.core.execution.api import create_execution_plan
from dagster.core.instance import DagsterInstance, InstanceRef
from dagster.core.launcher import LaunchRunContext, RunLauncher
from dagster.core.run_coordinator.queued_run_coordinator import QueuedRunCoordinator
from dagster.core.snap import (
    create_execution_plan_snapshot_id,
    create_pipeline_snapshot_id,
    snapshot_from_execution_plan,
)
from dagster.core.test_utils import create_run_for_test, environ, instance_for_test
from dagster.serdes import ConfigurableClass
from dagster.serdes.config_class import ConfigurableClassData
from dagster_tests.api_tests.utils import get_bar_workspace


def test_get_run_by_id():
    instance = DagsterInstance.ephemeral()

    assert instance.get_runs() == []
    pipeline_run = create_run_for_test(instance, pipeline_name="foo_pipeline", run_id="new_run")

    assert instance.get_runs() == [pipeline_run]

    assert instance.get_run_by_id(pipeline_run.run_id) == pipeline_run


def do_test_single_write_read(instance):
    run_id = "some_run_id"
    pipeline_def = PipelineDefinition(name="some_pipeline", solid_defs=[])
    instance.create_run_for_pipeline(pipeline_def=pipeline_def, run_id=run_id)
    run = instance.get_run_by_id(run_id)
    assert run.run_id == run_id
    assert run.pipeline_name == "some_pipeline"
    assert list(instance.get_runs()) == [run]
    instance.wipe()
    assert list(instance.get_runs()) == []


def test_filesystem_persist_one_run(tmpdir):
    with instance_for_test(temp_dir=str(tmpdir)) as instance:
        do_test_single_write_read(instance)


def test_in_memory_persist_one_run():
    with DagsterInstance.ephemeral() as instance:
        do_test_single_write_read(instance)


def test_create_pipeline_snapshot():
    @solid
    def noop_solid(_):
        pass

    @pipeline
    def noop_pipeline():
        noop_solid()

    with instance_for_test() as instance:
        result = execute_pipeline(noop_pipeline, instance=instance)
        assert result.success

        run = instance.get_run_by_id(result.run_id)

        assert run.pipeline_snapshot_id == create_pipeline_snapshot_id(
            noop_pipeline.get_pipeline_snapshot()
        )


def test_create_execution_plan_snapshot():
    @solid
    def noop_solid(_):
        pass

    @pipeline
    def noop_pipeline():
        noop_solid()

    with instance_for_test() as instance:
        execution_plan = create_execution_plan(noop_pipeline)

        ep_snapshot = snapshot_from_execution_plan(
            execution_plan, noop_pipeline.get_pipeline_snapshot_id()
        )
        ep_snapshot_id = create_execution_plan_snapshot_id(ep_snapshot)

        result = execute_pipeline(noop_pipeline, instance=instance)
        assert result.success

        run = instance.get_run_by_id(result.run_id)

        assert run.execution_plan_snapshot_id == ep_snapshot_id
        assert run.execution_plan_snapshot_id == create_execution_plan_snapshot_id(ep_snapshot)


def test_submit_run():
    with instance_for_test(
        overrides={
            "run_coordinator": {
                "module": "dagster.core.test_utils",
                "class": "MockedRunCoordinator",
            }
        }
    ) as instance:
        with get_bar_workspace(instance) as workspace:
            external_pipeline = (
                workspace.get_repository_location("bar_repo_location")
                .get_repository("bar_repo")
                .get_full_external_pipeline("foo")
            )

            run = create_run_for_test(
                instance=instance,
                pipeline_name=external_pipeline.name,
                run_id="foo-bar",
                external_pipeline_origin=external_pipeline.get_external_origin(),
                pipeline_code_origin=external_pipeline.get_python_origin(),
            )

            instance.submit_run(run.run_id, workspace)

            assert len(instance.run_coordinator.queue()) == 1
            assert instance.run_coordinator.queue()[0].run_id == "foo-bar"


def test_get_required_daemon_types():
    from dagster.daemon.daemon import (
        SensorDaemon,
        BackfillDaemon,
        SchedulerDaemon,
        MonitoringDaemon,
    )

    with instance_for_test() as instance:
        assert instance.get_required_daemon_types() == [
            SensorDaemon.daemon_type(),
            BackfillDaemon.daemon_type(),
            SchedulerDaemon.daemon_type(),
        ]

    with instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster_tests.daemon_tests.test_monitoring_daemon",
                "class": "TestRunLauncher",
            },
            "run_monitoring": {"enabled": True},
        }
    ) as instance:
        assert instance.get_required_daemon_types() == [
            SensorDaemon.daemon_type(),
            BackfillDaemon.daemon_type(),
            SchedulerDaemon.daemon_type(),
            MonitoringDaemon.daemon_type(),
        ]


def test_run_monitoring():
    with pytest.raises(CheckError):
        with instance_for_test(
            overrides={
                "run_monitoring": {"enabled": True},
            }
        ):
            pass

    settings = {"enabled": True}
    with instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster_tests.daemon_tests.test_monitoring_daemon",
                "class": "TestRunLauncher",
            },
            "run_monitoring": settings,
        }
    ) as instance:
        assert instance.run_monitoring_enabled
        assert instance.run_monitoring_settings == settings
        assert instance.run_monitoring_max_resume_run_attempts == 3

    settings = {"enabled": True, "max_resume_run_attempts": 5}
    with instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster_tests.daemon_tests.test_monitoring_daemon",
                "class": "TestRunLauncher",
            },
            "run_monitoring": settings,
        }
    ) as instance:
        assert instance.run_monitoring_enabled
        assert instance.run_monitoring_settings == settings
        assert instance.run_monitoring_max_resume_run_attempts == 5


def test_cancellation_thread():
    with instance_for_test(
        overrides={
            "run_monitoring": {"cancellation_thread_poll_interval_seconds": 300},
        }
    ) as instance:
        assert instance.cancellation_thread_poll_interval_seconds == 300

    with instance_for_test() as instance:
        assert instance.cancellation_thread_poll_interval_seconds == 10


def test_dagster_home_not_set():
    with environ({"DAGSTER_HOME": ""}):
        with pytest.raises(
            DagsterHomeNotSetError,
            match=r"The environment variable \$DAGSTER_HOME is not set\.",
        ):
            DagsterInstance.get()


def test_invalid_configurable_class():
    with pytest.raises(
        check.CheckError,
        match=re.escape(
            "Couldn't find class MadeUpRunLauncher in module when attempting to "
            "load the configurable class dagster.MadeUpRunLauncher"
        ),
    ):
        with instance_for_test(
            overrides={"run_launcher": {"module": "dagster", "class": "MadeUpRunLauncher"}}
        ):
            pass


def test_invalid_configurable_module():
    with pytest.raises(
        check.CheckError,
        match=re.escape(
            "Couldn't import module made_up_module when attempting to load "
            "the configurable class made_up_module.MadeUpRunLauncher",
        ),
    ):
        with instance_for_test(
            overrides={"run_launcher": {"module": "made_up_module", "class": "MadeUpRunLauncher"}}
        ):
            pass


@pytest.mark.parametrize("dirname", (".", ".."))
def test_dagster_home_not_abspath(dirname):
    with environ({"DAGSTER_HOME": dirname}):
        with pytest.raises(
            DagsterInvariantViolationError,
            match=re.escape('$DAGSTER_HOME "{}" must be an absolute path.'.format(dirname)),
        ):
            DagsterInstance.get()


def test_dagster_home_not_dir():
    dirname = "/this/path/does/not/exist"

    with environ({"DAGSTER_HOME": dirname}):
        with pytest.raises(
            DagsterInvariantViolationError,
            match=re.escape(
                '$DAGSTER_HOME "{}" is not a directory or does not exist.'.format(dirname)
            ),
        ):
            DagsterInstance.get()


class TestInstanceSubclass(DagsterInstance):
    def __init__(self, *args, foo=None, baz=None, **kwargs):
        self._foo = foo
        self._baz = baz
        super().__init__(*args, **kwargs)

    def foo(self):
        return self._foo

    @property
    def baz(self):
        return self._baz

    @classmethod
    def config_schema(cls):
        return {"foo": Field(str, is_required=True), "baz": Field(str, is_required=False)}

    @staticmethod
    def config_defaults(base_dir):
        defaults = InstanceRef.config_defaults(base_dir)
        defaults["run_coordinator"] = ConfigurableClassData(
            "dagster.core.run_coordinator.queued_run_coordinator",
            "QueuedRunCoordinator",
            yaml.dump({}),
        )
        return defaults


def test_instance_subclass():
    with instance_for_test(
        overrides={
            "instance_class": {
                "module": "dagster_tests.core_tests.instance_tests.test_instance",
                "class": "TestInstanceSubclass",
            },
            "foo": "bar",
        }
    ) as subclass_instance:
        assert isinstance(subclass_instance, DagsterInstance)

        # isinstance(subclass_instance, TestInstanceSubclass) does not pass
        # Likely because the imported/dynamically loaded class is different from the local one

        assert subclass_instance.__class__.__name__ == "TestInstanceSubclass"
        assert subclass_instance.foo() == "bar"
        assert subclass_instance.baz is None

        assert isinstance(subclass_instance.run_coordinator, QueuedRunCoordinator)

    with instance_for_test(
        overrides={
            "instance_class": {
                "module": "dagster_tests.core_tests.instance_tests.test_instance",
                "class": "TestInstanceSubclass",
            },
            "foo": "bar",
            "baz": "quux",
        }
    ) as subclass_instance:
        assert isinstance(subclass_instance, DagsterInstance)

        assert subclass_instance.__class__.__name__ == "TestInstanceSubclass"
        assert subclass_instance.foo() == "bar"
        assert subclass_instance.baz == "quux"

    # omitting foo leads to a config schema validation error

    with pytest.raises(DagsterInvalidConfigError):
        with instance_for_test(
            overrides={
                "instance_class": {
                    "module": "dagster_tests.core_tests.instance_tests.test_instance",
                    "class": "TestInstanceSubclass",
                },
                "baz": "quux",
            }
        ) as subclass_instance:
            pass


# class that doesn't implement needed methods on ConfigurableClass
class InvalidRunLauncher(RunLauncher, ConfigurableClass):
    def can_terminate(self, run_id):
        return False

    def launch_run(self, context: LaunchRunContext) -> None:
        pass

    def terminate(self, run_id):
        pass


def test_configurable_class_missing_methods():
    with pytest.raises(
        NotImplementedError,
        match="InvalidRunLauncher must implement the config_type classmethod",
    ):
        with instance_for_test(
            overrides={
                "run_launcher": {
                    "module": "dagster_tests.core_tests.instance_tests.test_instance",
                    "class": "InvalidRunLauncher",
                }
            }
        ):
            pass
