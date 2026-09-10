"""Tests for the retry helpers.

Concurrent table creation is the case these exist for: two processes starting at once both
run `create_all`, and one of them loses. Distinguishing "the object already exists" (fatal,
the caller must not loop) from a transient failure (retry) is done by parsing the native
SQL Server error number out of a pyodbc exception, which is worth pinning down.
"""

import pyodbc
import pytest
import sqlalchemy.exc as db_exc
from dagster_mssql.utils import (
    DagsterMSSQLException,
    error_numbers,
    is_fatal_connection_error,
    is_transient_error,
    retry_mssql_connection_fn,
    retry_mssql_creation_fn,
    retry_on_deadlock,
)

# The shape pyodbc actually raises: (sqlstate, message-with-native-errno-in-parens)
OBJECT_EXISTS = pyodbc.ProgrammingError(
    "42S01",
    "[42S01] [Microsoft][ODBC Driver 18 for SQL Server][SQL Server]There is already an "
    "object named 'runs' in the database. (2714) (SQLExecDirectW)",
)
DUPLICATE_INDEX = pyodbc.ProgrammingError(
    "42S11",
    "[42S11] [Microsoft][ODBC Driver 18 for SQL Server][SQL Server]The operation failed "
    "because an index or statistics with name 'idx_run_tags' already exists. (1913) "
    "(SQLExecDirectW)",
)
TRANSIENT = pyodbc.ProgrammingError(
    "08S01",
    "[08S01] [Microsoft][ODBC Driver 18 for SQL Server]Communication link failure (0)",
)

# Azure SQL raises these routinely -- during a failover, a service reconfiguration, or
# when the database is throttling. They are the reason the backoff is exponential.
AZURE_UNAVAILABLE = pyodbc.OperationalError(
    "HY000",
    "[HY000] [Microsoft][ODBC Driver 18 for SQL Server][SQL Server]Database 'dagster' on "
    "server 'x.database.windows.net' is not currently available. Please retry the "
    "connection later. (40613) (SQLDriverConnect)",
)
AZURE_BUSY = pyodbc.OperationalError(
    "HY000",
    "[HY000] [Microsoft][ODBC Driver 18 for SQL Server][SQL Server]The service is "
    "currently busy. Retry the request after 10 seconds. (40501) (SQLDriverConnect)",
)
AZURE_THROTTLED = pyodbc.OperationalError(
    "HY000",
    "[HY000] [Microsoft][ODBC Driver 18 for SQL Server][SQL Server]Resource ID : 1. The "
    "request limit for the database is 200 and has been reached. (10928) (SQLDriverConnect)",
)

# No amount of retrying fixes a rejected login.
BAD_PASSWORD = pyodbc.InterfaceError(
    "28000",
    "[28000] [Microsoft][ODBC Driver 18 for SQL Server][SQL Server]Login failed for user "
    "'dagster'. (18456) (SQLDriverConnect)",
)
NO_PERMISSION = pyodbc.ProgrammingError(
    "42000",
    "[42000] [Microsoft][ODBC Driver 18 for SQL Server][SQL Server]The server principal "
    '"dagster" is not able to access the database "dagster" under the current security '
    "context. (916) (SQLDriverConnect)",
)
FIREWALL = pyodbc.InterfaceError(
    "HY000",
    "[HY000] [Microsoft][ODBC Driver 18 for SQL Server][SQL Server]Cannot open server "
    "'x' requested by the login. Client with IP address '1.2.3.4' is not allowed to "
    "access the server. (40615) (SQLDriverConnect)",
)


def _raiser(*exceptions):
    """Raise each exception in turn, then return a sentinel."""
    remaining = list(exceptions)

    def fn():
        if remaining:
            raise remaining.pop(0)
        return "ok"

    return fn


class TestRetryCreation:
    def test_returns_immediately_on_success(self):
        assert retry_mssql_creation_fn(lambda: "ok") == "ok"

    @pytest.mark.parametrize("exc", [OBJECT_EXISTS, DUPLICATE_INDEX])
    def test_already_exists_is_raised_not_retried(self, exc):
        """The table is there, so retrying would spin until the limit and then mask the
        real cause behind a "too many retries" error.
        """
        calls = []

        def fn():
            calls.append(1)
            raise exc

        with pytest.raises(pyodbc.ProgrammingError):
            retry_mssql_creation_fn(fn, retry_limit=3, retry_wait=0)

        assert len(calls) == 1

    def test_sqlalchemy_wrapped_already_exists_is_raised(self):
        wrapped = db_exc.ProgrammingError("CREATE TABLE runs", {}, OBJECT_EXISTS)
        with pytest.raises(db_exc.ProgrammingError):
            retry_mssql_creation_fn(
                lambda: (_ for _ in ()).throw(wrapped), retry_limit=3, retry_wait=0
            )

    def test_transient_failure_is_retried(self):
        fn = _raiser(TRANSIENT, TRANSIENT)
        assert retry_mssql_creation_fn(fn, retry_limit=3, retry_wait=0) == "ok"

    def test_gives_up_after_retry_limit(self):
        def fn():
            raise TRANSIENT

        with pytest.raises(DagsterMSSQLException, match="too many retries"):
            retry_mssql_creation_fn(fn, retry_limit=2, retry_wait=0)


class TestRetryConnection:
    def test_returns_immediately_on_success(self):
        assert retry_mssql_connection_fn(lambda: "ok") == "ok"

    def test_retries_then_succeeds(self):
        fn = _raiser(
            pyodbc.OperationalError("HYT00", "Login timeout expired"),
            pyodbc.InterfaceError("08001", "Could not open a connection"),
        )
        assert retry_mssql_connection_fn(fn, retry_limit=3, retry_wait=0) == "ok"

    def test_gives_up_after_retry_limit(self):
        def fn():
            raise pyodbc.OperationalError("HYT00", "Login timeout expired")

        with pytest.raises(DagsterMSSQLException, match="too many retries"):
            retry_mssql_connection_fn(fn, retry_limit=2, retry_wait=0)

    @pytest.mark.parametrize("exc", [AZURE_UNAVAILABLE, AZURE_BUSY, AZURE_THROTTLED])
    def test_azure_transient_errors_are_retried(self, exc):
        fn = _raiser(exc, exc)
        assert retry_mssql_connection_fn(fn, retry_limit=3, retry_wait=0) == "ok"

    @pytest.mark.parametrize("exc", [BAD_PASSWORD, NO_PERMISSION, FIREWALL])
    def test_fatal_errors_are_raised_immediately(self, exc):
        """Retrying a rejected login burns the whole budget and then reports "too many
        retries", which reads as a network fault and hides the actual cause.
        """
        calls = []

        def fn():
            calls.append(1)
            raise exc

        with pytest.raises(type(exc)):
            retry_mssql_connection_fn(fn, retry_limit=5, retry_wait=0)

        assert len(calls) == 1

    def test_sqlalchemy_wrapped_fatal_error_is_raised_immediately(self):
        wrapped = db_exc.OperationalError("SELECT 1", {}, BAD_PASSWORD)
        calls = []

        def fn():
            calls.append(1)
            raise wrapped

        with pytest.raises(db_exc.OperationalError):
            retry_mssql_connection_fn(fn, retry_limit=5, retry_wait=0)

        assert len(calls) == 1

    def test_backoff_grows_and_is_capped(self, monkeypatch):
        slept = []
        monkeypatch.setattr("dagster_mssql.utils.time.sleep", slept.append)
        # full jitter samples [0, ceiling); pin it to the ceiling to observe the schedule
        monkeypatch.setattr("dagster_mssql.utils.random.uniform", lambda _lo, hi: hi)

        def fn():
            raise AZURE_UNAVAILABLE

        with pytest.raises(DagsterMSSQLException):
            retry_mssql_connection_fn(fn, retry_limit=6, retry_wait=1.0, max_retry_wait=8.0)

        assert slept == [1.0, 2.0, 4.0, 8.0, 8.0, 8.0]

    def test_backoff_is_jittered(self, monkeypatch):
        """Several dagster processes lose their connections at the same instant during a
        failover; backing off in lockstep would have them all return at the same instant.
        """
        ceilings = []
        monkeypatch.setattr("dagster_mssql.utils.time.sleep", lambda _: None)
        monkeypatch.setattr(
            "dagster_mssql.utils.random.uniform",
            lambda lo, hi: ceilings.append((lo, hi)) or 0,
        )

        def fn():
            raise AZURE_UNAVAILABLE

        with pytest.raises(DagsterMSSQLException):
            retry_mssql_connection_fn(fn, retry_limit=3, retry_wait=1.0)

        assert ceilings == [(0, 1.0), (0, 2.0), (0, 4.0)]


DEADLOCK = pyodbc.Error(
    "40001",
    "[40001] [Microsoft][ODBC Driver 18 for SQL Server][SQL Server]Transaction (Process "
    "ID 81) was deadlocked on lock resources with another process and has been chosen as "
    "the deadlock victim. Rerun the transaction. (1205) (SQLExecDirectW)",
)


class TestRetryOnDeadlock:
    """Deadlocks are routine here, not exceptional.

    Dagster's upserts run under SERIALIZABLE, where SQL Server locks a key range rather
    than a row, so concurrent writers collide even on rows they do not share. SQL Server's
    own message says what to do about it: rerun the transaction.
    """

    def test_returns_immediately_on_success(self):
        assert retry_on_deadlock(lambda: "ok") == "ok"

    def test_deadlock_victim_is_retried(self):
        fn = _raiser(DEADLOCK, DEADLOCK)
        assert retry_on_deadlock(fn, retry_limit=3, retry_wait=0) == "ok"

    def test_retries_sqlalchemy_wrapped_deadlock(self):
        wrapped = db_exc.OperationalError("MERGE kvs", {}, DEADLOCK)
        fn = _raiser(wrapped)
        assert retry_on_deadlock(fn, retry_limit=3, retry_wait=0) == "ok"

    def test_other_errors_are_not_retried(self):
        """Only a deadlock means "rerun and it may work"; anything else would loop for
        nothing and then be reported as a retry-limit failure.
        """
        calls = []

        def fn():
            calls.append(1)
            raise OBJECT_EXISTS

        with pytest.raises(pyodbc.ProgrammingError):
            retry_on_deadlock(fn, retry_limit=5, retry_wait=0)

        assert len(calls) == 1

    def test_gives_up_after_retry_limit(self):
        def fn():
            raise DEADLOCK

        with pytest.raises(DagsterMSSQLException, match="deadlock victim"):
            retry_on_deadlock(fn, retry_limit=2, retry_wait=0)

    def test_reruns_the_whole_callable(self):
        """The victim's transaction is already rolled back, so the retry has to redo all
        of it -- not just re-execute the statement that lost.
        """
        runs = []

        def fn():
            runs.append("start")
            if len(runs) < 3:
                raise DEADLOCK
            return "ok"

        assert retry_on_deadlock(fn, retry_limit=5, retry_wait=0) == "ok"
        assert runs == ["start", "start", "start"]


class TestErrorClassification:
    def test_extracts_every_parenthesised_number(self):
        # pyodbc puts the ODBC function name in parentheses too, next to the errno
        assert error_numbers(OBJECT_EXISTS) == frozenset({2714})

    def test_extracts_from_sqlalchemy_wrapper(self):
        wrapped = db_exc.ProgrammingError("CREATE TABLE runs", {}, OBJECT_EXISTS)
        assert error_numbers(wrapped) == frozenset({2714})

    def test_no_numbers(self):
        assert error_numbers(pyodbc.OperationalError("HYT00", "Login timeout expired")) == (
            frozenset()
        )

    def test_non_pyodbc_exception(self):
        assert error_numbers(ValueError("nope")) == frozenset()

    @pytest.mark.parametrize("exc", [BAD_PASSWORD, NO_PERMISSION, FIREWALL])
    def test_fatal_is_fatal(self, exc):
        assert is_fatal_connection_error(exc)
        assert not is_transient_error(exc)

    @pytest.mark.parametrize("exc", [AZURE_UNAVAILABLE, AZURE_BUSY, AZURE_THROTTLED, TRANSIENT])
    def test_transient_is_transient(self, exc):
        assert is_transient_error(exc)
        assert not is_fatal_connection_error(exc)

    def test_unknown_error_is_neither(self):
        """Unrecognised errors are retried, so they must not be classified as fatal."""
        unknown = pyodbc.OperationalError("HY000", "Something new happened (99999)")
        assert not is_fatal_connection_error(unknown)
        assert not is_transient_error(unknown)
