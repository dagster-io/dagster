import os

import dagster as dg
import pytest
from dagster._core.errors import DagsterInvalidSubsetError
from dagster._core.events import DagsterEventType
from dagster._core.execution.plan.resume_retry import ReexecutionStrategy
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.storage.tags import ASSET_RESUME_RETRY_TAG, RESUME_RETRY_TAG, SYSTEM_TAG_PREFIX
from dagster._core.test_utils import (
    environ,
    poll_for_finished_run,
    step_did_not_run,
    step_succeeded,
)
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster._core.workspace.load_target import PythonFileTarget

CONDITIONAL_FAIL_ENV = "DAGSTER_CONDIIONAL_FAIL"


@dg.op
def before_failure():
    return "hello"


@dg.op
def conditional_fail(_, input_value):
    if os.environ.get(CONDITIONAL_FAIL_ENV):
        raise Exception("env set, failing!")

    return input_value


@dg.op
def after_failure(_, input_value):
    return input_value


@dg.job(tags={"foo": "bar"})
def conditional_fail_job():
    after_failure(conditional_fail(before_failure()))


@dg.multi_asset(
    specs=[
        dg.AssetSpec("a", skippable=True),
        dg.AssetSpec("c", deps="b", skippable=True),
        dg.AssetSpec("d", deps=["a", "b"], skippable=True),
    ],
    can_subset=True,
)
def acd(context: dg.AssetExecutionContext):
    fail_output = os.environ.get(CONDITIONAL_FAIL_ENV)
    for selected in sorted(context.selected_output_names):
        if selected == fail_output:
            raise Exception("env set, failing!")
        yield dg.Output(None, selected)


@dg.asset(deps=["a"])
def b() -> None: ...


@dg.multi_asset(
    specs=[
        dg.AssetSpec("a_checked", skippable=True),
        dg.AssetSpec("c_checked", deps="b_checked", skippable=True),
        dg.AssetSpec("d_checked", deps=["a_checked", "b_checked"], skippable=True),
    ],
    check_specs=[
        dg.AssetCheckSpec("good", asset="a_checked"),
        dg.AssetCheckSpec("good", asset="c_checked"),
        dg.AssetCheckSpec("good", asset="d_checked"),
    ],
    can_subset=True,
)
def acd_checked(context: dg.AssetExecutionContext):
    context.log.info(f"{list(sorted(context.selected_output_names))}")
    fail_output = os.environ.get(CONDITIONAL_FAIL_ENV)
    for selected in sorted(context.selected_output_names):
        if selected == fail_output:
            raise Exception("env set, failing!")
        if selected.endswith("good"):
            yield dg.AssetCheckResult(asset_key=selected[:-5], check_name="good", passed=True)
        else:
            yield dg.Output(None, selected)


@dg.multi_asset(
    specs=[
        dg.AssetSpec("fail_after_materialize", skippable=True),
    ],
    can_subset=True,
)
def fail_after_materialize(context: dg.AssetExecutionContext):
    context.log.info(f"{list(sorted(context.selected_output_names))}")
    yield dg.AssetMaterialization(asset_key=dg.AssetKey("fail_after_materialize"))
    raise Exception("I have failed")


@dg.asset(deps=["a_checked"])
def b_checked() -> None: ...


@dg.asset_check(name="good", asset="b_checked")
def b_checked_good() -> dg.AssetCheckResult:
    return dg.AssetCheckResult(passed=True)


@dg.multi_asset(
    specs=[
        dg.AssetSpec("a1_blocking", skippable=True),
        dg.AssetSpec("a2_blocking", skippable=True),
    ],
    check_specs=[
        dg.AssetCheckSpec("good_a_nonblock", asset="a2_blocking", blocking=False),
        dg.AssetCheckSpec("good_b_block", asset="a2_blocking", blocking=True),
    ],
    can_subset=True,
)
def blocking_checked(context: dg.AssetExecutionContext):
    context.log.info(f"{list(sorted(context.selected_output_names))}")
    for selected in sorted(context.selected_output_names):
        if selected.endswith("block"):
            yield dg.AssetCheckResult(
                asset_key=selected[:11],
                check_name=selected[12:],
                passed=not bool(os.environ.get(CONDITIONAL_FAIL_ENV)),
            )
        else:
            yield dg.Output(None, selected)


@dg.asset(deps=["a1_blocking"])
def a1_blocking_downstream() -> None: ...


@dg.multi_asset(
    specs=[
        dg.AssetSpec("a1_unsubsettable"),
        dg.AssetSpec("a2_unsubsettable"),
    ],
    check_specs=[
        dg.AssetCheckSpec("good", asset="a1_unsubsettable"),
    ],
)
def unsubsettable_checked(context: dg.AssetExecutionContext):
    context.log.info(f"{list(sorted(context.selected_output_names))}")
    fail_output = os.environ.get(CONDITIONAL_FAIL_ENV)
    for selected in sorted(context.selected_output_names):
        if selected == fail_output:
            raise Exception("env set, failing!")
        if selected.endswith("good"):
            yield dg.AssetCheckResult(asset_key=selected[:-5], check_name="good", passed=True)
        else:
            yield dg.Output(None, selected)


@dg.asset(deps=["a1_unsubsettable"])
def a1_unsubsettable_downstream() -> None: ...


defs = dg.Definitions(
    assets=[
        acd,
        b,
        acd_checked,
        b_checked,
        b_checked_good,
        blocking_checked,
        a1_blocking_downstream,
        unsubsettable_checked,
        a1_unsubsettable_downstream,
        fail_after_materialize,
    ],
    jobs=[
        conditional_fail_job,
        dg.define_asset_job(name="multi_asset_fail_job", selection=[acd, b]),
        dg.define_asset_job(
            name="multi_asset_with_checks_fail_job",
            selection=[acd_checked, b_checked, b_checked_good],
        ),
        dg.define_asset_job(
            name="blocking_check_job",
            selection=[blocking_checked, a1_blocking_downstream],
        ),
        dg.define_asset_job(
            name="unsubsettable_job",
            selection=[unsubsettable_checked, a1_unsubsettable_downstream],
        ),
        dg.define_asset_job(
            name="fail_after_materialize_job",
            selection=[fail_after_materialize],
        ),
    ],
)


def multi_asset_fail_job():
    return defs.resolve_job_def("multi_asset_fail_job")


def multi_asset_with_checks_fail_job():
    return defs.resolve_job_def("multi_asset_with_checks_fail_job")


def blocking_check_job():
    return defs.resolve_job_def("blocking_check_job")


def unsubsettable_job():
    return defs.resolve_job_def("unsubsettable_job")


def fail_after_materialize_job():
    return defs.resolve_job_def("fail_after_materialize_job")


@pytest.fixture(name="instance", scope="module")
def instance_fixture():
    with dg.instance_for_test() as instance:
        yield instance


@pytest.fixture(name="workspace", scope="module")
def workspace_fixture(instance):
    with WorkspaceProcessContext(
        instance,
        PythonFileTarget(
            python_file=__file__,
            attribute=None,
            working_directory=None,
            location_name="repo_loc",
        ),
    ) as workspace_process_context:
        yield workspace_process_context.create_request_context()


@pytest.fixture(name="code_location", scope="module")
def code_location_fixture(workspace):
    return workspace.get_code_location("repo_loc")


@pytest.fixture(name="remote_job", scope="module")
def remote_job_fixture(code_location):
    return code_location.get_repository("__repository__").get_full_job("conditional_fail_job")


@pytest.fixture(name="failed_run", scope="module")
def failed_run_fixture(instance):
    # trigger failure in the conditionally_fail op
    with environ({CONDITIONAL_FAIL_ENV: "1"}):
        result = dg.execute_job(
            dg.reconstructable(conditional_fail_job),
            instance=instance,
            tags={"fizz": "buzz", "foo": "not bar!", f"{SYSTEM_TAG_PREFIX}run_metrics": "true"},
        )

    assert not result.success

    return instance.get_run_by_id(result.run_id)


@pytest.fixture(scope="module")
def success_run(instance):
    # trigger failure in the conditionally_fail op
    result = dg.execute_job(
        dg.reconstructable(conditional_fail_job),
        instance=instance,
        tags={"fizz": "buzz", "foo": "not bar!", f"{SYSTEM_TAG_PREFIX}run_metrics": "true"},
    )

    assert result.success

    return instance.get_run_by_id(result.run_id)


def test_create_reexecuted_run_from_failure(
    instance: dg.DagsterInstance, workspace, code_location, remote_job, failed_run
):
    run = instance.create_reexecuted_run(
        parent_run=failed_run,
        code_location=code_location,
        remote_job=remote_job,
        strategy=ReexecutionStrategy.FROM_FAILURE,
        request_context=workspace,
    )

    assert run.tags[RESUME_RETRY_TAG] == "true"
    assert set(run.step_keys_to_execute) == {"conditional_fail", "after_failure"}  # type: ignore
    instance.launch_run(run.run_id, workspace)
    run = poll_for_finished_run(instance, run.run_id)

    assert run.status == DagsterRunStatus.SUCCESS
    assert step_did_not_run(instance, run, "before_failure")
    assert step_succeeded(instance, run, "conditional_fail")
    assert step_succeeded(instance, run, "after_failure")


def test_create_reexecuted_run_from_failure_all_steps_succeeded(
    instance: dg.DagsterInstance, workspace, code_location, remote_job, success_run
):
    failed_after_finish_run = success_run._replace(status=DagsterRunStatus.FAILURE)

    with pytest.raises(
        DagsterInvalidSubsetError, match="No steps needed to be retried in the failed run."
    ):
        instance.create_reexecuted_run(
            parent_run=failed_after_finish_run,
            request_context=workspace,
            code_location=code_location,
            remote_job=remote_job,
            strategy=ReexecutionStrategy.FROM_FAILURE,
        )


def test_create_reexecuted_run_from_failure_tags(
    instance: dg.DagsterInstance,
    workspace,
    code_location,
    remote_job,
    failed_run,
):
    run = instance.create_reexecuted_run(
        parent_run=failed_run,
        request_context=workspace,
        code_location=code_location,
        remote_job=remote_job,
        strategy=ReexecutionStrategy.FROM_FAILURE,
    )

    assert run.tags["foo"] == "bar"
    assert "fizz" not in run.tags

    run = instance.create_reexecuted_run(
        parent_run=failed_run,
        request_context=workspace,
        code_location=code_location,
        remote_job=remote_job,
        strategy=ReexecutionStrategy.FROM_FAILURE,
        use_parent_run_tags=True,
    )

    assert run.tags["foo"] == "not bar!"
    assert run.tags["fizz"] == "buzz"

    run = instance.create_reexecuted_run(
        parent_run=failed_run,
        request_context=workspace,
        code_location=code_location,
        remote_job=remote_job,
        strategy=ReexecutionStrategy.FROM_FAILURE,
        use_parent_run_tags=True,
        extra_tags={"fizz": "not buzz!!"},
    )

    assert run.tags["foo"] == "not bar!"
    assert run.tags["fizz"] == "not buzz!!"
    assert f"{SYSTEM_TAG_PREFIX}run_metrics" not in run.tags


def test_create_reexecuted_run_all_steps(
    instance: dg.DagsterInstance, workspace, code_location, remote_job, failed_run
):
    run = instance.create_reexecuted_run(
        parent_run=failed_run,
        request_context=workspace,
        code_location=code_location,
        remote_job=remote_job,
        strategy=ReexecutionStrategy.ALL_STEPS,
    )

    assert RESUME_RETRY_TAG not in run.tags

    instance.launch_run(run.run_id, workspace)
    run = poll_for_finished_run(instance, run.run_id)

    assert run.status == DagsterRunStatus.SUCCESS
    assert step_succeeded(instance, run, "before_failure")
    assert step_succeeded(instance, run, "conditional_fail")
    assert step_succeeded(instance, run, "after_failure")


def _get_materialized_keys(instance: dg.DagsterInstance, run_id: str) -> set[dg.AssetKey]:
    result = instance.get_records_for_run(
        run_id=run_id, of_type=DagsterEventType.ASSET_MATERIALIZATION, limit=1000
    )
    keys = set()
    for record in result.records:
        assert record.asset_materialization
        keys.add(record.asset_materialization.asset_key)
    return keys


def _get_checked_keys(instance: dg.DagsterInstance, run_id: str) -> set[dg.AssetCheckKey]:
    result = instance.get_records_for_run(
        run_id=run_id, of_type=DagsterEventType.ASSET_CHECK_EVALUATION, limit=1000
    )
    keys = set()
    for record in result.records:
        dagster_event = record.event_log_entry.dagster_event
        assert dagster_event
        assert isinstance(dagster_event.event_specific_data, dg.AssetCheckEvaluation)
        keys.add(dagster_event.event_specific_data.asset_check_key)
    return keys


def test_create_reexecuted_run_from_multi_asset_failure(
    instance: dg.DagsterInstance, workspace, code_location
):
    remote_job = code_location.get_repository("__repository__").get_full_job("multi_asset_fail_job")
    with environ({CONDITIONAL_FAIL_ENV: "c"}):
        result = dg.execute_job(dg.reconstructable(multi_asset_fail_job), instance=instance)
        assert not result.success
        failed_run = instance.get_run_by_id(result.run_id)
        assert failed_run

    assert _get_materialized_keys(instance, failed_run.run_id) == {
        dg.AssetKey("a"),
        dg.AssetKey("b"),
    }
    run = instance.create_reexecuted_run(
        parent_run=failed_run,
        request_context=workspace,
        code_location=code_location,
        remote_job=remote_job,
        strategy=ReexecutionStrategy.FROM_ASSET_FAILURE,
    )

    assert run.tags[ASSET_RESUME_RETRY_TAG] == "true"
    instance.launch_run(run.run_id, workspace)
    run = poll_for_finished_run(instance, run.run_id)

    assert run.status == DagsterRunStatus.SUCCESS
    assert _get_materialized_keys(instance, run.run_id) == {dg.AssetKey("c"), dg.AssetKey("d")}


def test_create_reexecuted_run_from_multi_asset_check_failure(
    instance: dg.DagsterInstance, workspace, code_location
):
    remote_job = code_location.get_repository("__repository__").get_full_job(
        "multi_asset_with_checks_fail_job"
    )
    with environ({CONDITIONAL_FAIL_ENV: "c_checked"}):
        result = dg.execute_job(
            dg.reconstructable(multi_asset_with_checks_fail_job), instance=instance
        )
        assert not result.success
        failed_run = instance.get_run_by_id(result.run_id)
        assert failed_run

    assert _get_materialized_keys(instance, failed_run.run_id) == {
        dg.AssetKey("a_checked"),
    }
    assert _get_checked_keys(instance, failed_run.run_id) == {
        dg.AssetCheckKey(dg.AssetKey("a_checked"), "good"),
    }
    run = instance.create_reexecuted_run(
        parent_run=failed_run,
        request_context=workspace,
        code_location=code_location,
        remote_job=remote_job,
        strategy=ReexecutionStrategy.FROM_ASSET_FAILURE,
    )

    assert run.tags[ASSET_RESUME_RETRY_TAG] == "true"
    instance.launch_run(run.run_id, workspace)
    run = poll_for_finished_run(instance, run.run_id)

    assert run.status == DagsterRunStatus.SUCCESS
    assert _get_materialized_keys(instance, run.run_id) == {
        dg.AssetKey("b_checked"),
        dg.AssetKey("c_checked"),
        dg.AssetKey("d_checked"),
    }
    assert _get_checked_keys(instance, run.run_id) == {
        dg.AssetCheckKey(dg.AssetKey("b_checked"), "good"),
        dg.AssetCheckKey(dg.AssetKey("c_checked"), "good"),
        dg.AssetCheckKey(dg.AssetKey("d_checked"), "good"),
    }


def test_create_reexecuted_run_from_multi_asset_failure_after_all_assets_materialized(
    instance: dg.DagsterInstance, workspace, code_location
):
    remote_job = code_location.get_repository("__repository__").get_full_job(
        "fail_after_materialize_job"
    )
    result = dg.execute_job(dg.reconstructable(fail_after_materialize_job), instance=instance)
    assert not result.success
    failed_run = instance.get_run_by_id(result.run_id)
    assert failed_run
    assert _get_materialized_keys(instance, failed_run.run_id) == {
        dg.AssetKey("fail_after_materialize"),
    }
    with pytest.raises(
        DagsterInvalidSubsetError,
        match="No assets or asset checks needed to be retried in the failed run.",
    ):
        instance.create_reexecuted_run(
            parent_run=failed_run,
            request_context=workspace,
            code_location=code_location,
            remote_job=remote_job,
            strategy=ReexecutionStrategy.FROM_ASSET_FAILURE,
        )


def test_create_reexecuted_run_from_multi_asset_check_failure_blocking_check(
    instance: dg.DagsterInstance, workspace, code_location
):
    remote_job = code_location.get_repository("__repository__").get_full_job("blocking_check_job")
    with environ({CONDITIONAL_FAIL_ENV: "1"}):
        result = dg.execute_job(dg.reconstructable(blocking_check_job), instance=instance)
        assert not result.success
        failed_run = instance.get_run_by_id(result.run_id)
        assert failed_run

    assert _get_materialized_keys(instance, failed_run.run_id) == {
        dg.AssetKey("a1_blocking"),
        dg.AssetKey("a2_blocking"),
    }
    assert _get_checked_keys(instance, failed_run.run_id) == {
        dg.AssetCheckKey(dg.AssetKey("a2_blocking"), "good_a_nonblock"),
        dg.AssetCheckKey(dg.AssetKey("a2_blocking"), "good_b_block"),
    }
    run = instance.create_reexecuted_run(
        parent_run=failed_run,
        request_context=workspace,
        code_location=code_location,
        remote_job=remote_job,
        strategy=ReexecutionStrategy.FROM_ASSET_FAILURE,
    )

    assert run.tags[ASSET_RESUME_RETRY_TAG] == "true"
    instance.launch_run(run.run_id, workspace)
    run = poll_for_finished_run(instance, run.run_id)

    assert run.status == DagsterRunStatus.SUCCESS
    assert _get_materialized_keys(instance, run.run_id) == {
        # a2_blocking is re-executed because its blocking check failed
        dg.AssetKey("a2_blocking"),
        dg.AssetKey("a1_blocking_downstream"),
    }
    assert _get_checked_keys(instance, run.run_id) == {
        # a2_blocking_good is re-executed because it is a failed blocking check
        dg.AssetCheckKey(dg.AssetKey("a2_blocking"), "good_b_block"),
        # a2_blocking_good_nonblock is re-executed because its asset got re-executed
        dg.AssetCheckKey(dg.AssetKey("a2_blocking"), "good_a_nonblock"),
    }


def test_create_reexecuted_run_from_multi_asset_check_failure_unsubsettable(
    instance: dg.DagsterInstance, workspace, code_location
):
    remote_job = code_location.get_repository("__repository__").get_full_job("unsubsettable_job")
    with environ({CONDITIONAL_FAIL_ENV: "a2_unsubsettable"}):
        result = dg.execute_job(dg.reconstructable(unsubsettable_job), instance=instance)
        assert not result.success
        failed_run = instance.get_run_by_id(result.run_id)
        assert failed_run

    assert _get_materialized_keys(instance, failed_run.run_id) == {
        dg.AssetKey("a1_unsubsettable"),
    }
    assert _get_checked_keys(instance, failed_run.run_id) == {
        dg.AssetCheckKey(dg.AssetKey("a1_unsubsettable"), "good"),
    }
    run = instance.create_reexecuted_run(
        parent_run=failed_run,
        request_context=workspace,
        code_location=code_location,
        remote_job=remote_job,
        strategy=ReexecutionStrategy.FROM_ASSET_FAILURE,
    )

    assert run.tags[ASSET_RESUME_RETRY_TAG] == "true"
    instance.launch_run(run.run_id, workspace)
    run = poll_for_finished_run(instance, run.run_id)

    assert run.status == DagsterRunStatus.SUCCESS
    assert _get_materialized_keys(instance, run.run_id) == {
        dg.AssetKey("a1_unsubsettable"),
        dg.AssetKey("a2_unsubsettable"),
        dg.AssetKey("a1_unsubsettable_downstream"),
    }
    assert _get_checked_keys(instance, run.run_id) == {
        dg.AssetCheckKey(dg.AssetKey("a1_unsubsettable"), "good"),
    }
