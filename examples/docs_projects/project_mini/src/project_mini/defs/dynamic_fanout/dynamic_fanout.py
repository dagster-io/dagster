import multiprocessing
from typing import Any

import dagster as dg

# =============================================================================
# GENERIC DATA PROCESSING PIPELINE CONFIGURATION
# =============================================================================


class DataProcessingConfig(dg.Config):
    input_data_path: str
    processing_threshold: float = 0.5


# Helper functions for your domain logic
def extract_processing_units(record: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract 10-30 processing units from a single data record."""
    # Replace with your actual unit extraction logic
    num_units = min(30, max(10, hash(record["id"]) % 20 + 10))
    units = [
        {"unit_data": f"unit_{i}", "properties": [i * 10, i * 10, 50, 50]} for i in range(num_units)
    ]
    return units


def process_single_unit(unit_data: dict[str, Any]) -> dict[str, Any]:
    """Process a single data unit (your expensive computation)."""
    # Replace with your actual unit processing logic
    return {"processed": True, "result": f"processed_{unit_data}"}


def aggregate_unit_results(
    record: dict[str, Any], unit_results: list[dict[str, Any]]
) -> dict[str, Any]:
    """Combine unit processing results into final record output."""
    # Replace with your actual aggregation logic
    return {
        "record_id": record["id"],
        "aggregated_output": f"combined_result_from_{len(unit_results)}_units",
        "output_data": unit_results,
    }


# =============================================================================
# MAIN PIPELINE IMPLEMENTATION
# =============================================================================


@dg.asset
def input_records(config: DataProcessingConfig) -> list[dict[str, Any]]:
    """MAIN PIPELINE: Load multiple related data records for processing."""
    # Replace with your actual data loading logic
    records = [
        {"id": f"record_{i}", "data_path": f"path/to/data_{i}.dat"}
        for i in range(5)  # Your multiple related records
    ]
    return records


# =============================================================================
# SUB-PIPELINE OPERATIONS
# =============================================================================


@dg.op(out=dg.DynamicOut())
def trigger_sub_pipelines(context: dg.OpExecutionContext, input_records: list[dict[str, Any]]):
    """MAIN PIPELINE: Launch sub-pipeline for each record individually
    (First layer of parallelization).

    "The sub_pipelines are triggered based on the number of inputs"
    """
    context.log.info(f"Launching {len(input_records)} sub-pipelines based on input count")

    # Each record triggers one sub-pipeline
    for record in input_records:
        yield dg.DynamicOutput(record, mapping_key=record["id"])


# Option A
@dg.op
def sub_pipeline_process_record_option_a(
    context: dg.OpExecutionContext, record: dict[str, Any]
) -> dict[str, Any]:
    """SUB-PIPELINE: Complete processing workflow for a single data record.

    1. "Extract processing units from the record (10-30 units per record)"
    2. "Each unit goes through processing (Second layer of parallelization)"
       [Currently sequential as specified]
    3. "Results are aggregated to create final record output"
    """
    context.log.info(f"Sub-pipeline processing record: {record['id']}")

    # Step 1: Extract processing units from record (10-30 units)
    processing_units = extract_processing_units(record)
    context.log.info(f"Extracted {len(processing_units)} units from {record['id']}")

    # Step 2: Process each unit (Second layer of parallelization)
    # Currently sequential as specified, but can be parallelized when ready
    unit_results = []

    # Sequential processing (current implementation)
    for i, unit in enumerate(processing_units):
        context.log.info(f"Processing unit {i + 1}/{len(processing_units)} for {record['id']}")
        result = process_single_unit(unit)
        unit_results.append(result)

    # Step 3: Aggregate results to create final record output
    aggregated_output = aggregate_unit_results(record, unit_results)

    context.log.info(
        f"Sub-pipeline completed for {record['id']}: aggregated {len(unit_results)} unit results"
    )

    return {
        "record_id": record["id"],
        "sub_pipeline_result": aggregated_output,
        "units_processed": len(unit_results),
        "original_record": record,
    }


# Option B
@dg.op
def sub_pipeline_process_record_option_b(
    context: dg.OpExecutionContext, record: dict[str, Any]
) -> dict[str, Any]:
    """SUB-PIPELINE: Complete processing workflow for a single data record.

    1. "Extract processing units from the record (10-30 units per record)"
    2. "Each unit goes through processing (Second layer of parallelization)"
       [Implemented using multiprocessing pool]
    3. "Results are aggregated to create final record output"
    """
    context.log.info(f"Sub-pipeline processing record: {record['id']}")

    # Step 1: Extract processing units from record (10-30 units)
    processing_units = extract_processing_units(record)
    context.log.info(f"Extracted {len(processing_units)} units from {record['id']}")

    # Step 2: Process each unit (Second layer of parallelization)
    # Currently sequential as specified, but can be parallelized when ready
    unit_results = []

    # Parallel processing (enable when ready for second layer)
    def process_unit_worker(unit):
        return process_single_unit(unit)

    if len(processing_units) > 1:
        num_processes = min(multiprocessing.cpu_count() - 1, len(processing_units))
        with multiprocessing.Pool(processes=num_processes) as pool:
            unit_results = pool.map(process_unit_worker, processing_units)
    else:
        unit_results = [process_unit_worker(processing_units[0])] if processing_units else []

    # Step 3: Aggregate results to create final record output
    aggregated_output = aggregate_unit_results(record, unit_results)

    context.log.info(
        f"Sub-pipeline completed for {record['id']}: aggregated {len(unit_results)} unit results"
    )

    return {
        "record_id": record["id"],
        "sub_pipeline_result": aggregated_output,
        "units_processed": len(unit_results),
        "original_record": record,
    }


@dg.op
def collect_sub_pipeline_results(
    context: dg.OpExecutionContext, sub_pipeline_results: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """MAIN PIPELINE: "The individual results are then collected for additional processing".

    "The main pipeline's goal is to collect the results of the sub pipelines,
     so it cannot be completed before all sub_pipelines return their results"
    """
    context.log.info(f"Collecting results from {len(sub_pipeline_results)} sub-pipelines")
    context.log.info("Main pipeline waited for ALL sub-pipelines to complete before proceeding")

    # Additional processing on collected results
    processed_results = []
    for result in sub_pipeline_results:
        # Example: additional processing on each sub-pipeline result
        enhanced_result = {
            **result,
            "collection_timestamp": "2025-08-25T10:00:00Z",
            "processed_by_main_pipeline": True,
        }
        processed_results.append(enhanced_result)

    return processed_results


# =============================================================================
# MAIN PIPELINE AS GRAPH-BACKED ASSET
# =============================================================================


@dg.graph_asset
def main_pipeline_results(input_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """COMPLETE MAIN PIPELINE.

    1. ✅ Receives multiple related data records.
    2. ✅ sub_pipeline processes each record individually (First layer of parallelization)
    3. ✅ Individual results are collected for additional processing
    4. ✅ Generate final results (used by downstream assets for final report)

    The graph-backed asset ensures:
    - Sub-pipelines are triggered based on number of inputs
    - Main pipeline cannot complete before ALL sub-pipelines return results
    - Full visibility into parallel execution
    - Proper asset lineage and dependencies
    """
    # Launch sub-pipelines (one per input record)
    sub_pipeline_triggers = trigger_sub_pipelines(input_records)

    # Execute sub-pipelines in parallel (first layer of parallelization)
    sub_pipeline_results = sub_pipeline_triggers.map(sub_pipeline_process_record_option_a)

    # Collect ALL results before proceeding (fan-in / synchronization barrier)
    collected_results = sub_pipeline_results.collect()  # This waits for all to complete

    # Perform additional processing and return final results
    return collect_sub_pipeline_results(collected_results)


@dg.asset
def final_report(main_pipeline_results: list[dict[str, Any]]) -> dict[str, Any]:
    """MAIN PIPELINE: "generate a comprehensive final report".

    This asset depends on main_pipeline_results, ensuring the entire pipeline
    completes before the final report is generated.
    """
    total_units = sum(result["units_processed"] for result in main_pipeline_results)

    return {
        "pipeline_summary": {
            "total_records_processed": len(main_pipeline_results),
            "total_units_processed": total_units,
            "average_units_per_record": total_units / len(main_pipeline_results)
            if main_pipeline_results
            else 0,
        },
        "detailed_results": main_pipeline_results,
        "report_generated_at": "2025-08-25T10:00:00Z",
        "pipeline_status": "completed_successfully",
    }
