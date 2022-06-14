from dagster import build_op_context
from docs_snippets.concepts.assets.materialization_ops import (
    my_asset_key_materialization_op,
    my_materialization_op,
    my_metadata_materialization_op,
    my_partitioned_asset_op,
    my_simple_op,
)


def test_ops_compile_and_execute():
    ops = [
        (my_asset_key_materialization_op, True),
        (my_materialization_op, True),
        (my_metadata_materialization_op, True),
        (my_simple_op, False),
    ]

    for op, has_context_arg in ops:
        op(None) if has_context_arg else op()  # pylint: disable=expression-not-assigned


def test_partition_config_ops_compile_and_execute():
    ops = [
        my_partitioned_asset_op,
    ]

    for op in ops:
        context = build_op_context(config={"date": "2020-01-01"})

        op(context)
