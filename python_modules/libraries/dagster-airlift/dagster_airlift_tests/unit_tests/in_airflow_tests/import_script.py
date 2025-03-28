import_failed = False
try:
    import dagster as dagster
except ImportError:
    import_failed = True
if not import_failed:
    raise Exception("Importing dagster did not fail")

requires_airflow = False
try:
    from dagster_airlift.in_airflow import AirflowProxiedState as AirflowProxiedState
except Exception as e:
    if "Airflow is not installed" in str(e):
        requires_airflow = True
if not requires_airflow:
    raise Exception("Importing dagster_airlift.in_airflow did not fail")
