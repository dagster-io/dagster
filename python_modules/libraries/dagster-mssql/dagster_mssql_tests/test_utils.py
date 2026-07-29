"""Tests for the retry helpers.

Concurrent table creation is the case these exist for: two processes starting at once both
run `create_all`, and one of them loses. Distinguishing "the object already exists" (fatal,
the caller must not loop) from a transient failure (retry) is done by parsing the native
SQL Server error number out of a pyodbc exception, which is worth pinning down.
"""

import pytest
import pyodbc
import sqlalchemy.exc as db_exc
from dagster_mssql.utils import (
    DagsterMSSQLException,
    retry_mssql_connection_fn,
    retry_mssql_creation_fn,
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
            retry_mssql_creation_fn(lambda: (_ for _ in ()).throw(wrapped), retry_limit=3, retry_wait=0)

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
