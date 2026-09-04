from collections.abc import Sequence
from uuid import UUID, uuid4

import pytest
from dagster import AssetExecutionContext, asset, materialize
from dagster._core.errors import DagsterExecutionInterruptedError, DagsterPipesExecutionError
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.pipes.client import PipesContextInjector, PipesMessageReader
from dagster._core.pipes.context import PipesSession
from dagster._core.pipes.utils import PipesTempFileContextInjector, PipesTempFileMessageReader
from dagster_prefect.pipes import BasePipesPrefectClient, PrefectRun
from dagster_prefect.resource import PrefectResource
from prefect import flow, task
from prefect.client.schemas.objects import State, StateType
from prefect.runtime import task_run as task_run_runtime
from prefect.states import Cancelled, Completed, Crashed, Failed, Running

# The scripted client never reaches the API, so point it somewhere that would fail loudly
# if it ever did.
UNREACHABLE_API_URL = "http://127.0.0.1:1/api"


class StubPipesPrefectClient(BasePipesPrefectClient):
    """Fills in the abstract hooks without launching anything.

    The Pipes session is real; only the hand-off to Prefect is stubbed out.
    """

    def __init__(self, *, prefect_run: PrefectRun | None = None, **kwargs):
        super().__init__(**kwargs)
        self._prefect_run = prefect_run
        self.launched: list[PrefectRun] = []

    def _launch(
        self,
        *,
        context: OpExecutionContext | AssetExecutionContext,
        session: PipesSession,
        **kwargs,
    ) -> PrefectRun:
        prefect_run = self._prefect_run or PrefectRun(kind="flow-run", id=uuid4())
        self.launched.append(prefect_run)
        return prefect_run

    def _default_context_injector(self) -> PipesContextInjector:
        return PipesTempFileContextInjector()

    def _default_message_reader(self) -> PipesMessageReader:
        return PipesTempFileMessageReader()


class ScriptedStatesClient(StubPipesPrefectClient):
    """Reads back a scripted sequence of states instead of asking Prefect.

    The last state repeats, so a sequence must end in a terminal state or polling never
    exits.
    """

    def __init__(self, states: Sequence[State | None], **kwargs):
        super().__init__(**kwargs)
        self._states = list(states)
        self.reads = 0

    def _read_state(self, prefect_run: PrefectRun) -> State | None:
        self.reads += 1
        return self._states[min(self.reads - 1, len(self._states) - 1)]


def scripted_client(*states: State | None) -> ScriptedStatesClient:
    return ScriptedStatesClient(
        states=states,
        prefect=PrefectResource(api_url=UNREACHABLE_API_URL),
        poll_interval_seconds=0,
    )


def materialize_with(client: BasePipesPrefectClient):
    @asset
    def prefect_backed(context: AssetExecutionContext):
        return client.run(context=context).get_materialize_result()

    return materialize([prefect_backed], raise_on_error=True)


def test_completed_run_materializes() -> None:
    client = scripted_client(Completed())

    result = materialize_with(client)

    assert result.success
    assert len(result.get_asset_materialization_events()) == 1
    assert len(client.launched) == 1


def test_polls_until_final() -> None:
    client = scripted_client(Running(), Running(), Completed())

    assert materialize_with(client).success
    assert client.reads == 3


@pytest.mark.parametrize(
    "state",
    [Failed(message="it broke"), Crashed(message="the worker died"), Cancelled()],
    ids=["failed", "crashed", "cancelled"],
)
def test_unsuccessful_final_state_raises(state: State) -> None:
    with pytest.raises(DagsterPipesExecutionError, match="Prefect flow-run"):
        materialize_with(scripted_client(state))


def test_failure_reports_the_prefect_message() -> None:
    with pytest.raises(DagsterPipesExecutionError, match="deployment has no work pool"):
        materialize_with(scripted_client(Failed(message="deployment has no work pool")))


def test_failure_without_a_message_still_names_the_state() -> None:
    with pytest.raises(DagsterPipesExecutionError, match=r"finished as StateType\.CANCELLED"):
        materialize_with(scripted_client(Cancelled()))


def test_injector_and_reader_can_be_overridden() -> None:
    client = ScriptedStatesClient(
        states=[Completed()],
        prefect=PrefectResource(api_url=UNREACHABLE_API_URL),
        context_injector=PipesTempFileContextInjector(),
        message_reader=PipesTempFileMessageReader(),
        poll_interval_seconds=0,
    )

    assert materialize_with(client).success


# Reading state is the one piece the scripted subclass replaces, so it gets its own tests
# against a real Prefect API.
@flow(name="reads-back")
def reads_back() -> int:
    return 1


@task
def report_task_run_id() -> str:
    return task_run_runtime.id


@flow(name="reads-back-with-task")
def reads_back_with_task() -> str:
    return report_task_run_id()


def test_read_state_of_a_real_flow_run(prefect_resource: PrefectResource) -> None:
    with prefect_resource.get_client() as prefect_client:
        flow_run = prefect_client.create_flow_run(reads_back)
    client = StubPipesPrefectClient(prefect=prefect_resource)

    state = client._read_state(PrefectRun(kind="flow-run", id=flow_run.id))  # noqa: SLF001

    assert state is not None
    assert flow_run.state is not None
    assert state.type == flow_run.state.type


def test_read_state_of_a_real_task_run(prefect_resource: PrefectResource) -> None:
    task_run_id = reads_back_with_task()
    client = StubPipesPrefectClient(prefect=prefect_resource)

    state = client._read_state(PrefectRun(kind="task-run", id=UUID(task_run_id)))  # noqa: SLF001

    assert state is not None
    assert state.is_completed()


def test_metadata_carries_the_prefect_run_id_and_url() -> None:
    prefect_run = PrefectRun(kind="flow-run", id=uuid4())
    client = ScriptedStatesClient(
        states=[Completed()],
        prefect=PrefectResource(api_url=UNREACHABLE_API_URL),
        prefect_run=prefect_run,
        poll_interval_seconds=0,
    )

    result = materialize_with(client)

    metadata = result.get_asset_materialization_events()[0].materialization.metadata
    assert metadata["Prefect Run ID"].value == str(prefect_run.id)
    assert metadata["Prefect Run URL"].value == (
        f"http://127.0.0.1:1/runs/flow-run/{prefect_run.id}"
    )


def test_metadata_url_points_at_the_task_run_for_a_task() -> None:
    prefect_run = PrefectRun(kind="task-run", id=uuid4())
    client = ScriptedStatesClient(
        states=[Completed()],
        prefect=PrefectResource(api_url=UNREACHABLE_API_URL),
        prefect_run=prefect_run,
        poll_interval_seconds=0,
    )

    result = materialize_with(client)

    metadata = result.get_asset_materialization_events()[0].materialization.metadata
    assert metadata["Prefect Run URL"].value == (
        f"http://127.0.0.1:1/runs/task-run/{prefect_run.id}"
    )


def test_the_run_url_is_logged_at_launch(capsys: pytest.CaptureFixture[str]) -> None:
    prefect_run = PrefectRun(kind="flow-run", id=uuid4())
    client = ScriptedStatesClient(
        states=[Running(), Completed()],
        prefect=PrefectResource(api_url=UNREACHABLE_API_URL),
        prefect_run=prefect_run,
        poll_interval_seconds=0,
    )

    materialize_with(client)

    # Logged before polling starts, so the link is available while the run is in flight.
    assert f"runs/flow-run/{prefect_run.id}" in capsys.readouterr().err


class InterruptedClient(StubPipesPrefectClient):
    """Stands in for the Dagster run being terminated while waiting on Prefect."""

    def _read_state(self, prefect_run: PrefectRun) -> State | None:
        raise DagsterExecutionInterruptedError()


def _interrupted_client(prefect_resource: PrefectResource, prefect_run: PrefectRun, **kwargs):
    return InterruptedClient(
        prefect=prefect_resource,
        prefect_run=prefect_run,
        poll_interval_seconds=0,
        **kwargs,
    )


def test_termination_cancels_the_prefect_flow_run(prefect_resource: PrefectResource) -> None:
    with prefect_resource.get_client() as prefect_client:
        flow_run = prefect_client.create_flow_run(reads_back)
    client = _interrupted_client(prefect_resource, PrefectRun(kind="flow-run", id=flow_run.id))

    with pytest.raises(DagsterExecutionInterruptedError):
        materialize_with(client)

    state = prefect_resource.get_flow_run(flow_run.id).state
    assert state is not None
    assert state.type in (StateType.CANCELLING, StateType.CANCELLED)


def test_forward_termination_can_be_turned_off(prefect_resource: PrefectResource) -> None:
    with prefect_resource.get_client() as prefect_client:
        flow_run = prefect_client.create_flow_run(reads_back)
    client = _interrupted_client(
        prefect_resource, PrefectRun(kind="flow-run", id=flow_run.id), forward_termination=False
    )

    with pytest.raises(DagsterExecutionInterruptedError):
        materialize_with(client)

    state = prefect_resource.get_flow_run(flow_run.id).state
    assert state is not None
    assert state.type not in (StateType.CANCELLING, StateType.CANCELLED)


def test_termination_warns_that_a_task_run_keeps_running(
    prefect_resource: PrefectResource, capsys: pytest.CaptureFixture[str]
) -> None:
    task_run = PrefectRun(kind="task-run", id=uuid4())
    client = _interrupted_client(prefect_resource, task_run)

    with pytest.raises(DagsterExecutionInterruptedError):
        materialize_with(client)

    assert "cannot be cancelled" in capsys.readouterr().err
