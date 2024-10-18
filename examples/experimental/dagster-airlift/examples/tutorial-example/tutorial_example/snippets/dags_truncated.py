# Dags file can be found at tutorial_example/airflow_dags/dags.py
from pathlib import Path

from airflow import DAG
from dagster_airlift.in_airflow import proxying_to_dagster
from dagster_airlift.in_airflow.proxied_state import load_proxied_state_from_yaml

dag = DAG("rebuild_customers_list", ...)

...

# Set this to True to begin the proxying process
PROXYING = False

if PROXYING:
    proxying_to_dagster(
        global_vars=globals(),
        proxied_state=load_proxied_state_from_yaml(Path(__file__).parent / "proxied_state"),
    )
