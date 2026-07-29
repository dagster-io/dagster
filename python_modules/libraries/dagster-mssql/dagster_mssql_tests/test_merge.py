"""Tests for the MERGE-based upsert that stands in for ON CONFLICT / ON DUPLICATE KEY."""

import pytest
import sqlalchemy as db
from dagster._core.storage.runs.schema import DaemonHeartbeatsTable, KeyValueStoreTable
from dagster_mssql.merge import merge_statement
from sqlalchemy.dialects import mssql


def _sql(statement) -> str:
    return str(statement.compile(dialect=mssql.dialect()))


class TestMergeStatement:
    def test_holdlock_is_present(self):
        """Without HOLDLOCK two concurrent sessions can both miss the match and both
        insert, which surfaces as a duplicate key violation or a deadlock. This is the
        single most important property of the generated statement.
        """
        statement = merge_statement(
            KeyValueStoreTable, match_on=["key"], values={"key": "k", "value": "v"}
        )
        assert "WITH (HOLDLOCK)" in _sql(statement)

    def test_terminated_with_semicolon(self):
        # SQL Server requires MERGE to be terminated with a semicolon
        statement = merge_statement(
            KeyValueStoreTable, match_on=["key"], values={"key": "k", "value": "v"}
        )
        assert _sql(statement).rstrip().endswith(";")

    def test_reserved_words_are_quoted(self):
        # `key` and `value` are reserved words in T-SQL
        statement = merge_statement(
            KeyValueStoreTable, match_on=["key"], values={"key": "k", "value": "v"}
        )
        sql = _sql(statement)
        assert "[key]" in sql
        assert "[value]" in sql

    def test_match_columns_excluded_from_update(self):
        statement = merge_statement(
            KeyValueStoreTable, match_on=["key"], values={"key": "k", "value": "v"}
        )
        sql = _sql(statement)
        update_clause = sql.split("WHEN MATCHED THEN UPDATE SET")[1].split("WHEN NOT MATCHED")[0]
        assert "[value]" in update_clause
        assert "[key]" not in update_clause

    def test_explicit_update_values(self):
        statement = merge_statement(
            DaemonHeartbeatsTable,
            match_on=["daemon_type"],
            values={"daemon_type": "SCHEDULER", "daemon_id": "a", "body": "b"},
            update_values={"daemon_id": "z"},
        )
        sql = _sql(statement)
        update_clause = sql.split("WHEN MATCHED THEN UPDATE SET")[1].split("WHEN NOT MATCHED")[0]
        assert "[daemon_id]" in update_clause
        assert "[body]" not in update_clause

    def test_multi_row(self):
        statement = merge_statement(
            KeyValueStoreTable,
            match_on=["key"],
            values=[{"key": "a", "value": "1"}, {"key": "b", "value": "2"}],
        )
        # one VALUES tuple per row, one bind per column per row
        assert len(statement._bindparams) == 4  # noqa: SLF001
        assert _sql(statement).count("VALUES") == 2  # the USING source and the INSERT

    def test_bind_params_use_column_types(self):
        """Parameters must be bound with the column's type so the NVARCHAR variants apply;
        binding as VARCHAR would route non-ASCII through the database codepage.
        """
        statement = merge_statement(
            KeyValueStoreTable, match_on=["key"], values={"key": "k", "value": "v"}
        )
        bound = statement._bindparams  # noqa: SLF001
        # src_0_0 is the `key` column of the first (only) row
        key_type = bound["src_0_0"].type.compile(dialect=mssql.dialect())
        assert key_type.upper().startswith("NVARCHAR")

    def test_identifier_injection_is_escaped(self):
        table = db.Table(
            "weird]name",
            db.MetaData(),
            db.Column("a]b", db.String(10)),
            db.Column("v", db.String(10)),
        )
        sql = _sql(merge_statement(table, match_on=["a]b"], values={"a]b": "x", "v": "y"}))
        assert "[weird]]name]" in sql
        assert "[a]]b]" in sql

    def test_rejects_empty_rows(self):
        with pytest.raises(ValueError, match="at least one row"):
            merge_statement(KeyValueStoreTable, match_on=["key"], values=[])

    def test_rejects_unknown_match_column(self):
        with pytest.raises(ValueError, match="not present"):
            merge_statement(KeyValueStoreTable, match_on=["nope"], values={"key": "k"})

    def test_rejects_ragged_rows(self):
        with pytest.raises(ValueError, match="same columns"):
            merge_statement(
                KeyValueStoreTable,
                match_on=["key"],
                values=[{"key": "a", "value": "1"}, {"key": "b"}],
            )

    def test_no_update_clause_when_nothing_to_update(self):
        # a table whose only column is the match key has nothing to SET
        statement = merge_statement(KeyValueStoreTable, match_on=["key"], values={"key": "k"})
        sql = _sql(statement)
        assert "WHEN MATCHED" not in sql
        assert "WHEN NOT MATCHED THEN INSERT" in sql
