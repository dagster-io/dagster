from dagster_airlift.core import AirflowInstance, build_defs_from_airflow_instance
from dagster_airlift.mwaa import MwaaSessionAuthBackend

defs = build_defs_from_airflow_instance(
    airflow_instance=AirflowInstance(
        name="example-instance",
        auth_backend=MwaaSessionAuthBackend.from_profile(
            region="us-west-2", env_name="airlift-mwaa-example", profile_name="dev-cloud-admin"
        ),
    )
)
