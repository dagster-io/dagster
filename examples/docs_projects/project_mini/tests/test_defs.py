"""Smoke tests for project_mini module imports.

Full defs loading is skipped because project_mini uses dagster internal APIs
not yet released on PyPI. Pure-function coverage is in test_pii.py and test_assets.py.
"""

from dagster import Definitions
from project_mini.defs.dynamic_fanout.dynamic_fanout import (  # ty: ignore[unresolved-import]
    aggregate_unit_results,
    extract_processing_units,
    final_report,
    process_single_unit,
)
from project_mini.defs.dynamic_vs_parallel.dynamic_outputs import (  # ty: ignore[unresolved-import]
    defs as dynamic_outputs_defs,
)
from project_mini.defs.dynamic_vs_parallel.python_parallelism import (  # ty: ignore[unresolved-import]
    defs as python_parallelism_defs,
)
from project_mini.defs.partitions_vs_config.with_config import (  # ty: ignore[unresolved-import]
    CustomerConfig,
    customer_orders,
)
from project_mini.defs.pii_compute_logs.pii_redactor import (
    redact_pii,  # ty: ignore[unresolved-import]
)


def test_pii_redactor_importable():
    assert callable(redact_pii)


def test_dynamic_fanout_importable():
    assert callable(extract_processing_units)
    assert callable(process_single_unit)
    assert callable(aggregate_unit_results)
    assert callable(final_report)


def test_dynamic_vs_parallel_defs_load_together():
    Definitions.validate_loadable(Definitions.merge(dynamic_outputs_defs, python_parallelism_defs))


def test_customer_orders_importable():
    assert callable(customer_orders)
    assert CustomerConfig is not None
