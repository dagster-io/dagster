#!/usr/bin/env python3
"""A simple data processing script that would be executed by the PythonScriptComponent.
This script demonstrates basic data processing with Dagster pipes integration.
"""

from dagster_pipes import PipesContext, open_dagster_pipes


def main():
    with open_dagster_pipes() as context:
        # Simulate some data processing work
        context.log.info("Starting data processing...")

        # Example: Process some data (this would be your actual business logic)
        processed_records = 1000
        context.log.info(f"Processed {processed_records} records")

        # Report materialization back to Dagster
        context.report_asset_materialization(
            asset_key="processed_data",
            metadata={
                "records_processed": processed_records,
                "processing_time_seconds": 45.2,
                "data_quality_score": 0.98,
            },
        )

        context.log.info("Data processing completed successfully!")


if __name__ == "__main__":
    main()
