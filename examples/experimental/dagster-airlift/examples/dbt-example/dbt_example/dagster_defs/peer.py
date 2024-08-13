#### STEP 1: Peering ####
# In the first step, we peer with the running airflow instance, and automatically, airflow dags show up in Dagster as assets.
# When a run in airflow successfully completes, the corresponding dagster asset is updated with a new materialization.
# This is a read-only operation, and no code changes are necessary on the airflow side. Only REST API access from 
# Airflow is required, which is available on Airflow 2.0.0 and above (in the case of MWAA, it is available on 2.4.3 and above).
from dagster_airlift.core import AirflowInstance, BasicAuthBackend, build_defs_from_airflow_instance

from .constants import AIRFLOW_BASE_URL, AIRFLOW_INSTANCE_NAME, PASSWORD, USERNAME

# The airflow instance contains two components; a name, and an authentication backend.
# As of now, we support the following backends:
# 1. BasicAuthBackend (default session auth in airflow)
# 2. MwaaAuthBackend (MWAA specific auth, part of dagster-airlift[mwaa] submodule)
airflow_instance = AirflowInstance(
    auth_backend=BasicAuthBackend(
        webserver_url=AIRFLOW_BASE_URL, username=USERNAME, password=PASSWORD
    ),
    name=AIRFLOW_INSTANCE_NAME,
)

# Each dag in the airflow instance is represented as a dagster asset with a key of the form:
# - <airflow-instance-name>/dags/<dag-id>
# These assets are external, meaning they cannot be computed by dagster. Dagster will instead record
# materializations by polling the airflow instance for runs with the sensor `airflow_dag_status_sensor`.
defs = build_defs_from_airflow_instance(airflow_instance=airflow_instance)
