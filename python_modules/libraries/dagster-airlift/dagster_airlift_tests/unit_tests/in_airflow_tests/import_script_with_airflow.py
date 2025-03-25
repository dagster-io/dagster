import_failed = False
try:
    import dagster as dagster
except ImportError:
    import_failed = True
if not import_failed:
    raise Exception("Importing dagster did not fail")

from dagster_airlift.in_airflow import AirflowProxiedState as AirflowProxiedState
