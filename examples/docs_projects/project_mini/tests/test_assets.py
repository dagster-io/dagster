from typing import Any

import dagster as dg
from project_mini.defs.dynamic_fanout.dynamic_fanout import (
    aggregate_unit_results,
    extract_processing_units,
    final_report,
    process_single_unit,
)
from project_mini.defs.partitions_vs_config.with_config import CustomerConfig, customer_orders

# --- dynamic_fanout helper functions ---


def test_extract_processing_units_returns_list():
    record = {"id": "record_0"}
    units = extract_processing_units(record)
    assert isinstance(units, list)
    assert 10 <= len(units) <= 30


def test_extract_processing_units_structure():
    record = {"id": "record_1"}
    units = extract_processing_units(record)
    for unit in units:
        assert "unit_data" in unit
        assert "properties" in unit


def test_process_single_unit():
    unit = {"unit_data": "test_unit", "properties": [0, 0, 50, 50]}
    result = process_single_unit(unit)
    assert result["processed"] is True
    assert "result" in result


def test_aggregate_unit_results():
    record: dict[str, Any] = {"id": "record_x"}
    unit_results = [{"processed": True, "result": "r1"}, {"processed": True, "result": "r2"}]
    output = aggregate_unit_results(record, unit_results)
    assert output["record_id"] == "record_x"
    assert "aggregated_output" in output
    assert len(output["output_data"]) == 2


def test_final_report_summary():
    mock_results = [
        {
            "record_id": "r1",
            "units_processed": 5,
            "sub_pipeline_result": {},
            "original_record": {},
        },
        {
            "record_id": "r2",
            "units_processed": 3,
            "sub_pipeline_result": {},
            "original_record": {},
        },
    ]
    report = final_report(mock_results)
    assert report["pipeline_summary"]["total_records_processed"] == 2
    assert report["pipeline_summary"]["total_units_processed"] == 8
    assert report["pipeline_summary"]["average_units_per_record"] == 4.0
    assert report["pipeline_status"] == "completed_successfully"


def test_final_report_empty_input():
    report = final_report([])
    assert report["pipeline_summary"]["total_records_processed"] == 0
    assert report["pipeline_summary"]["total_units_processed"] == 0
    assert report["pipeline_summary"]["average_units_per_record"] == 0


# --- config-driven asset ---


def test_customer_orders_with_config():
    context = dg.build_asset_context()
    config = CustomerConfig(customer_id="C001")
    orders = customer_orders(context, config)
    assert len(orders) == 3
    assert orders[0]["order_id"] == "C001-001"
    assert all("amount" in o for o in orders)


def test_customer_orders_order_ids_prefixed_with_customer():
    context = dg.build_asset_context()
    config = CustomerConfig(customer_id="ACME")
    orders = customer_orders(context, config)
    assert all(o["order_id"].startswith("ACME-") for o in orders)
