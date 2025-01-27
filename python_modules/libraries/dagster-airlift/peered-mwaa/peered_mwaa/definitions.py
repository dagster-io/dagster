import os
import time

import boto3
from dagster._core.definitions.sensor_definition import DefaultSensorStatus
from dagster_airlift.core import AirflowInstance, build_defs_from_airflow_instance
from dagster_airlift.mwaa import MwaaSessionAuthBackend

boto_session = boto3.Session(
    profile_name=os.environ["MWAA_PROFILE"], region_name=os.environ["MWAA_REGION"]
)
af_instance = AirflowInstance(
    auth_backend=MwaaSessionAuthBackend(
        mwaa_client=boto_session.client("mwaa"),
        env_name=os.environ["MWAA_ENV_NAME"],
    ),
    name="my_instance",
)

print("Attempting to load repository...")
load_start_time = time.time()
defs = build_defs_from_airflow_instance(
    airflow_instance=af_instance, default_sensor_status=DefaultSensorStatus.STOPPED
)
load_end_time = time.time()
print(f"Time to load repository: {load_end_time - load_start_time} seconds")

# print("Launching 1000 runs...")
# launch_start_time = time.time()
# runs = set()
# for i in range(1000):
#     runs.add(af_instance.trigger_dag(f"dag_{i}"))

# while runs:
#     run_id = runs.pop()
#     af_instance.wait_for_run_completion(dag_id=f"dag_{i}", run_id=run_id)
# launch_end_time = time.time()
