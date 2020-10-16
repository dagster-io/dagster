from dagster.core.storage.event_log import schema as event_log_schema
from dagster.core.storage.runs import schema as run_schema


def assert_cols_equal(a_cols, b_cols, attr_name):
    b_cols_by_name = {col.name: col for col in b_cols}
    for a_col in a_cols:
        assert a_col.name in b_cols_by_name
        b_col = b_cols_by_name[a_col.name]
        assert str(getattr(a_col, attr_name)) == str(getattr(b_col, attr_name))


def test_secondary_index_schema():
    for col_attr in ["name", "type", "nullable", "primary_key", "foreign_keys", "unique"]:
        assert_cols_equal(
            event_log_schema.SecondaryIndexMigrationTable.columns,
            run_schema.SecondaryIndexMigrationTable.columns,
            col_attr,
        )
