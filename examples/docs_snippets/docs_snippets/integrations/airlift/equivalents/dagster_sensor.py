import json
from pathlib import Path

from dagster import RunRequest, SensorEvaluationContext, SkipReason, asset, sensor


@asset
def uploaded_customers_data():
    pass


# Implementing the FileSensor from Airflow directly in Dagster
@sensor(target=uploaded_customers_data)
def wait_for_new_files(context: SensorEvaluationContext):
    seen_files: list = json.loads(context.cursor) if context.cursor else []
    should_trigger = False
    for file in Path("path/to/customer_files").iterdir():
        if file.name not in seen_files:
            seen_files.append(file.name)
            should_trigger = True
    yield RunRequest() if should_trigger else SkipReason("No new files")
