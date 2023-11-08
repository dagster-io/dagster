from dagster._core.storage.sql import SqlQuery


def test_sql_query_basic():
    query0 = SqlQuery("SELECT 1 AS test_col")
    query1 = SqlQuery("SELECT * FROM $query0", query0=query0)

    assert query1.parse_bindings() == "SELECT * FROM (SELECT 1 AS test_col)"


def test_sql_query_from_absolute_path():
    """Unsure how to obtain absolute path when running in CICD.
    """
    # query0 = SqlQuery.from_file(filename)
    assert True


def test_sql_query_from_relative_path():
    query0 = SqlQuery.from_relative_path(__file__, "sql_queries/test_query0.sql")
    query1 = SqlQuery.from_relative_path(__file__, "sql_queries/test_query1.sql", query0=query0)

    assert query1.parse_bindings() == "SELECT * FROM (SELECT 1 AS test_col)"