import datetime
import random

from dagster import MaterializeResult, TableColumn, TableSchema, asset


@asset(
    owners=["claire@dagsterlabs.com"],
    tags={"tag_key": "value", "foo": "bar"},
    compute_kind="dbt",
    description="asset_one_description",
    group_name="group1",
)
def column_schema_asset():
    table_schema = TableSchema(
        columns=[
            TableColumn(f"asset-1-col-{datetime.datetime.now()!s}", "string"),
            TableColumn("col-2", "string"),
        ]
    )

    yield MaterializeResult(metadata={"dagster/column_schema": table_schema})


@asset(
    owners=["claire@dagsterlabs.com", "marco@dagsterlabs.com"],
    tags={"key_only_tag": ""},
    compute_kind="pandas",
    description="asset_two_description",
    group_name="group2",
)
def column_schema_asset_2():
    table_schema = TableSchema(
        columns=[
            TableColumn(f"asset-2-col-{datetime.datetime.now()!s}", "string"),
            TableColumn("col-2", "string"),
        ]
    )

    yield MaterializeResult(metadata={"dagster/column_schema": table_schema})


@asset(
    tags={"key_only_tag": "", "foo": "baz"},
    compute_kind="Plot",
    description="random_columns_asset_description",
    group_name="random",
)
def random_columns_asset():
    selected_numbers = set()
    random_columns = []
    for _ in range(30):
        number = random.randint(0, 30)
        if number in selected_numbers:
            continue
        random_columns.append(TableColumn(f"col-{number!s}", "string"))
        selected_numbers.add(number)

    table_schema = TableSchema(columns=list(random_columns))

    yield MaterializeResult(metadata={"dagster/column_schema": table_schema})
