"""Smoke tests for project_mini module imports.

Full defs loading is skipped because project_mini uses dagster internal APIs
not yet released on PyPI. Pure-function coverage is in test_pii.py and test_assets.py.
"""

from project_mini.defs.dynamic_fanout.dynamic_fanout import (
    aggregate_unit_results,
    extract_processing_units,
    final_report,
    process_single_unit,
)
from project_mini.defs.partitions_vs_config.with_config import CustomerConfig, customer_orders
from project_mini.defs.pii_compute_logs.pii_redactor import redact_pii


def test_pii_redactor_importable():
    assert callable(redact_pii)


def test_dynamic_fanout_importable():
    assert callable(extract_processing_units)
    assert callable(process_single_unit)
    assert callable(aggregate_unit_results)
    assert callable(final_report)


def test_customer_orders_importable():
    assert callable(customer_orders)
    assert CustomerConfig is not None
