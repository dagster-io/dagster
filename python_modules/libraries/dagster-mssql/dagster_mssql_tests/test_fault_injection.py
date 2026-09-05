"""Drive real storage operations through injected failures.

`test_utils.py` already covers the retry helpers, but it drives synthetic callables. That
leaves the question these tests answer: when a *real* storage write hits one of these
errors, does it recover, and does the data land correctly afterwards?

The errors injected here are the ones Azure SQL Database raises in normal operation --
throttling, reconfiguration, failover -- carrying the native error numbers and the message
shape pyodbc actually produces. Injecting them is not the same as observing them: this
proves how `dagster-mssql` handles those failures, not that Azure produces exactly these.
Azure remains untested against directly, since none of this behaviour is reproducible on a
local SQL Server.
"""

import pyodbc
import pytest
import sqlalchemy as db
import sqlalchemy.exc
from dagster._core.utils import make_new_run_id
from dagster._daemon.types import DaemonHeartbeat
from dagster._time import get_current_timestamp
from dagster_mssql.run_storage import MSSQLRunStorage
from dagster_mssql.utils import DagsterMSSQLException

# (errno, description) for the failures Azure raises routinely. The message layout matches
# pyodbc's: driver banner, text, then the native number in parentheses.
AZURE_TRANSIENT = [
    (40613, "Database is not currently available"),
    (40501, "The service is currently busy"),
    (40197, "The service has encountered an error processing your request"),
    (10928, "Resource ID: 1. The request limit for the database is 200"),
    (10929, "The %% minimum guarantee is 1, maximum limit is 200"),
    (49918, "Cannot process request. Not enough resources"),
    (49919, "Cannot process create or update request. Too many operations in progress"),
    (49920, "Cannot process request. Too many operations in progress"),
    (4060, "Cannot open database requested by the login"),
    (40143, "The service has encountered an error"),
    (40540, "The service has encountered an error"),
    (42108, "Can not connect to the SQL pool since it is paused"),
    (42109, "The SQL pool is warming up"),
    (10053, "A transport-level error has occurred"),
    (10054, "A transport-level error has occurred"),
    (10060, "A network-related or instance-specific error"),
    (233, "No process is on the other end of the pipe"),
    (64, "A connection was successfully established, but then an error occurred"),
]

AZURE_FATAL = [
    (18456, "Login failed for user 'dagster'"),
    (40615, "Cannot open server. Client with IP address '1.2.3.4' is not allowed"),
    (916, "The server principal is not able to access the database"),
]


def azure_error(errno: int, text: str) -> pyodbc.Error:
    return pyodbc.OperationalError(
        "HY000",
        f"[HY000] [Microsoft][ODBC Driver 18 for SQL Server][SQL Server]{text}. "
        f"({errno}) (SQLDriverConnect)",
    )


class Injector:
    """Counts connection attempts and fails the first `times` of them."""

    def __init__(self, exc, times: int):
        self.exc = exc
        self.remaining = times
        self.attempts = 0


def inject_connect_failures(storage, exc, times: int) -> Injector:
    """Fail `storage`'s next `times` connection attempts with `exc`.

    Patches `connect` on the real Engine rather than wrapping it: the storage classes
    type-check the engine, and swapping in a stand-in would test the stand-in. This sits
    exactly where `retry_mssql_connection_fn` calls it, so the retry runs for real.
    """
    engine = storage._engine  # noqa: SLF001
    original = engine.connect
    state = Injector(exc, times)

    def flaky(*args, **kwargs):
        state.attempts += 1
        if state.remaining > 0:
            state.remaining -= 1
            raise state.exc
        return original(*args, **kwargs)

    engine.connect = flaky
    return state


def inject_statement_failures(storage, exc, times: int, matching: str = "MERGE") -> Injector:
    """Fail `storage`'s next `times` executions of a statement containing `matching`.

    Distinct from `inject_connect_failures` in the way that matters: the connection is
    already open by the time this fires, so `retry_mssql_connection_fn` is out of the
    picture and only a transaction-level retry can recover. That is the case
    `inject_connect_failures` structurally cannot reach.
    """
    engine = storage._engine  # noqa: SLF001
    state = Injector(exc, times)

    @db.event.listens_for(engine, "before_cursor_execute")
    def _fail(_conn, _cursor, statement, _params, _context, _executemany):
        if matching in statement and state.remaining > 0:
            state.remaining -= 1
            state.attempts += 1
            raise state.exc

    return state


@pytest.fixture
def storage(conn_string):
    return MSSQLRunStorage.create_clean_storage(conn_string)


class TestTransientFailuresRecover:
    @pytest.mark.parametrize(
        "errno,text", AZURE_TRANSIENT, ids=[str(e) for e, _ in AZURE_TRANSIENT]
    )
    def test_write_survives_a_transient_error(self, storage, errno, text):
        """The write must land, not merely avoid raising."""
        flaky = inject_connect_failures(storage, azure_error(errno, text), times=2)

        storage.set_cursor_values({f"cursor_{errno}": "recovered"})

        assert flaky.attempts > 2, "the failure was never injected"
        assert storage.get_cursor_values({f"cursor_{errno}"}) == {f"cursor_{errno}": "recovered"}

    def test_heartbeat_survives_a_transient_error(self, storage):
        inject_connect_failures(storage, azure_error(40613, "unavailable"), times=2)

        storage.add_daemon_heartbeat(
            DaemonHeartbeat(
                timestamp=get_current_timestamp(),
                daemon_type="SENSOR",
                daemon_id=make_new_run_id(),
                errors=[],
            )
        )
        assert set(storage.get_daemon_heartbeats()) == {"SENSOR"}

    def test_exhausting_the_budget_raises_rather_than_hanging(self, storage):
        """A permanently unavailable database must fail, not retry forever."""
        inject_connect_failures(
            storage, azure_error(40613, "Database is not currently available"), times=10_000
        )

        with pytest.raises(DagsterMSSQLException, match="too many retries"):
            storage.set_cursor_values({"never": "lands"})


class TestFatalFailuresDoNotRetry:
    @pytest.mark.parametrize("errno,text", AZURE_FATAL, ids=[str(e) for e, _ in AZURE_FATAL])
    def test_fatal_error_surfaces_immediately(self, storage, errno, text):
        """A rejected login must not be reported as a retry-limit failure.

        Spending the budget first turns a credentials problem into what reads as a network
        problem, which is the wrong thing to hand somebody at 3am.
        """
        flaky = inject_connect_failures(storage, azure_error(errno, text), times=10_000)

        with pytest.raises(pyodbc.Error) as exc:
            storage.set_cursor_values({"fatal": "no"})

        assert str(errno) in str(exc.value)
        assert flaky.attempts == 1, f"retried a fatal error {flaky.attempts} times"


class TestDeadlockRecovery:
    """Deadlock is the one failure we have actually observed rather than injected.

    See `test_concurrency.py`. This covers the boundary that test cannot: that the retry
    reruns the whole transaction and the write still lands.
    """

    def test_injected_deadlock_recovers_with_data_intact(self, storage, conn_string):
        deadlock = pyodbc.Error(
            "40001",
            "[40001] [Microsoft][ODBC Driver 18 for SQL Server][SQL Server]Transaction "
            "(Process ID 55) was deadlocked on lock resources with another process and has "
            "been chosen as the deadlock victim. Rerun the transaction. (1205) "
            "(SQLExecDirectW)",
        )
        inject_connect_failures(storage, deadlock, times=3)

        storage.set_cursor_values({"deadlocked": "survived"})
        assert storage.get_cursor_values({"deadlocked"}) == {"deadlocked": "survived"}


def test_every_transient_errno_is_classified():
    """The injected list must stay in step with what the code actually recognises.

    A code added to one and not the other would leave a real Azure failure retried by
    accident or not at all.
    """
    from dagster_mssql.utils import _TRANSIENT_ERRNOS

    injected = {errno for errno, _ in AZURE_TRANSIENT}
    unclassified = injected - set(_TRANSIENT_ERRNOS)
    assert not unclassified, f"injected but not treated as transient: {sorted(unclassified)}"


def test_injected_errors_carry_a_parseable_errno():
    """Guards the tests themselves: a message pyodbc would not produce proves nothing."""
    from dagster_mssql.utils import error_numbers

    for errno, text in AZURE_TRANSIENT + AZURE_FATAL:
        assert errno in error_numbers(azure_error(errno, text))


class TestMidTransactionFailuresRecover:
    """Failures that land after the connection is open.

    `retry_mssql_connection_fn` guards `engine.connect` only, so once a statement is
    executing it offers nothing. Recovery here depends entirely on the transaction-level
    retry rerunning the whole block. These were missed originally because the only
    injection point available failed at connect time, where the connection-level retry
    hides the gap.
    """

    @pytest.mark.parametrize(
        "errno,text",
        [(40197, "The service has encountered an error"), (40613, "not currently available")],
        ids=["40197", "40613"],
    )
    def test_upsert_survives_a_mid_transaction_failure(self, storage, errno, text):
        flaky = inject_statement_failures(storage, azure_error(errno, text), times=2)

        storage.set_cursor_values({f"midflight_{errno}": "recovered"})

        assert flaky.attempts == 2, "the failure was never injected"
        assert storage.get_cursor_values({f"midflight_{errno}"}) == {
            f"midflight_{errno}": "recovered"
        }

    def test_heartbeat_survives_a_mid_transaction_failure(self, storage):
        flaky = inject_statement_failures(
            storage, azure_error(40501, "The service is currently busy"), times=2
        )

        storage.add_daemon_heartbeat(
            DaemonHeartbeat(
                timestamp=get_current_timestamp(),
                daemon_type="SENSOR",
                daemon_id=make_new_run_id(),
                errors=[],
            )
        )
        assert flaky.attempts == 2
        assert set(storage.get_daemon_heartbeats()) == {"SENSOR"}

    def test_fatal_error_mid_transaction_still_surfaces_immediately(self, storage):
        flaky = inject_statement_failures(
            storage, azure_error(916, "not able to access the database"), times=10_000
        )

        with pytest.raises((pyodbc.Error, db.exc.DBAPIError)):
            storage.set_cursor_values({"fatal_midflight": "no"})

        assert flaky.attempts == 1, f"retried a fatal error {flaky.attempts} times"
