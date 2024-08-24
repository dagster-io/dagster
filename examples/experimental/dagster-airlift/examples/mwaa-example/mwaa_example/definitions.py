from dagster_airlift.core import AirflowInstance, sync_build_defs_from_airflow_instance
from dagster_airlift.mwaa import MwaaSessionAuthBackend

defs = sync_build_defs_from_airflow_instance(
    airflow_instance=AirflowInstance(
        name="example-instance",
        auth_backend=MwaaSessionAuthBackend(
            region="us-west-2", env_name="airlift-mwaa-example", profile_name="dev-cloud-admin"
        ),
    )
)
