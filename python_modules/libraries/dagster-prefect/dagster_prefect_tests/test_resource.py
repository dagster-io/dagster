import pytest
from dagster._core.errors import DagsterInvariantViolationError
from dagster_prefect.resource import PrefectResource, is_final_state, is_successful_state
from prefect import flow, task
from prefect.client.schemas.objects import StateType
from prefect.runtime import task_run as task_run_runtime
from prefect.states import Cancelled, Completed, Crashed, Failed, Running, State

FLOW_RUN_ID = "11111111-1111-1111-1111-111111111111"


@flow(name="record-order")
def record_order(as_of: str = "latest") -> str:
    return as_of


@task
def report_task_run_id() -> str:
    return task_run_runtime.id


@flow(name="with-a-task")
def with_a_task() -> str:
    return report_task_run_id()


@pytest.fixture
def deployment_name(prefect_resource: PrefectResource) -> str:
    """Register a deployment through the API. Nothing runs it — no work pool, no worker."""
    with prefect_resource.get_client() as client:
        flow_id = client.create_flow(record_order)
        client.create_deployment(flow_id, name="test")
    return "record-order/test"


def test_launch_deployment_run(prefect_resource: PrefectResource, deployment_name: str) -> None:
    flow_run = prefect_resource.launch_deployment_run(
        deployment_name,
        parameters={"as_of": "2026-09-01"},
        tags=["dagster"],
    )

    assert flow_run.parameters == {"as_of": "2026-09-01"}
    assert "dagster" in flow_run.tags

    read_back = prefect_resource.get_flow_run(flow_run.id)
    assert read_back.id == flow_run.id
    assert read_back.deployment_id == flow_run.deployment_id
    assert not is_final_state(read_back.state)


def test_launch_deployment_run_unknown_deployment(prefect_resource: PrefectResource) -> None:
    # Prefect reports a missing deployment with an empty message; a malformed name it
    # already reports clearly on its own.
    with pytest.raises(
        DagsterInvariantViolationError, match='No Prefect deployment named "nope/nope"'
    ):
        prefect_resource.launch_deployment_run("nope/nope")


def test_cancel_flow_run(prefect_resource: PrefectResource, deployment_name: str) -> None:
    flow_run = prefect_resource.launch_deployment_run(deployment_name)

    prefect_resource.cancel_flow_run(flow_run.id)

    canceled = prefect_resource.get_flow_run(flow_run.id)
    assert canceled.state is not None
    assert canceled.state.type in (StateType.CANCELLING, StateType.CANCELLED)


def test_get_task_run(prefect_resource: PrefectResource) -> None:
    task_run_id = with_a_task()

    task_run = prefect_resource.get_task_run(task_run_id)

    assert str(task_run.id) == task_run_id
    assert is_successful_state(task_run.state)


# Both URL tests take `prefect_api_url` so the ambient Prefect settings point somewhere
# else entirely: the resource's own config has to win over whatever the environment says.
def test_run_urls_derived_from_api_url(prefect_api_url: str) -> None:
    resource = PrefectResource(api_url="http://127.0.0.1:4200/api")

    assert (
        resource.flow_run_url(FLOW_RUN_ID) == f"http://127.0.0.1:4200/runs/flow-run/{FLOW_RUN_ID}"
    )
    assert (
        resource.task_run_url(FLOW_RUN_ID) == f"http://127.0.0.1:4200/runs/task-run/{FLOW_RUN_ID}"
    )


def test_run_url_prefers_explicit_ui_url(prefect_api_url: str) -> None:
    resource = PrefectResource(
        api_url="https://api.prefect.cloud/api/accounts/acct/workspaces/ws",
        ui_url="https://app.prefect.cloud/account/acct/workspace/ws",
    )

    assert resource.flow_run_url(FLOW_RUN_ID) == (
        f"https://app.prefect.cloud/account/acct/workspace/ws/runs/flow-run/{FLOW_RUN_ID}"
    )


@pytest.mark.parametrize(
    ("state", "successful", "final"),
    [
        (Completed(), True, True),
        (Failed(), False, True),
        (Crashed(), False, True),
        (Cancelled(), False, True),
        (Running(), False, False),
        (None, False, False),
    ],
    ids=["completed", "failed", "crashed", "cancelled", "running", "missing"],
)
def test_state_mapping(state: State | None, successful: bool, final: bool) -> None:
    assert is_successful_state(state) is successful
    assert is_final_state(state) is final
