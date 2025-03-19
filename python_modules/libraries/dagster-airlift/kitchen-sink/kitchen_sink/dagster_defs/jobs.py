from kitchen_sink.airflow_instance import local_airflow_instance
from kitchen_sink.dagster_defs.utils import build_defs_from_airflow_instance_v2, migrate_runs

af_instance = local_airflow_instance()

defs = build_defs_from_airflow_instance_v2(af_instance)

# Migrates runs from Airflow to Dagster. You could imagine this is a CLI or something.
# `dagster-airlift migrate runs`
migrate_runs()
