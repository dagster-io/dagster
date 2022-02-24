from dagster import build_op_context
from docs_snippets.concepts.assets.observations import (
    observation_op,
    observes_dataset_op,
    partitioned_dataset_op,
)


def test_ops_compile_and_execute():
    observation_op(None)
    observes_dataset_op(None)

    context = build_op_context(config={"date": "2020-01-01"})
    partitioned_dataset_op(context)
