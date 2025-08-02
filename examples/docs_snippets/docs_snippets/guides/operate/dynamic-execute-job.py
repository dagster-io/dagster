from dagster import execute_job, reconstructable, DagsterInstance
import os

# Setup instance if needed
if not os.getenv("DAGSTER_HOME"):
    os.environ["DAGSTER_HOME"] = "./.dagster_test"
    os.makedirs("./.dagster_test", exist_ok=True)

instance = DagsterInstance.get()
result = execute_job(reconstructable(my_dynamic_job), instance=instance)
# True parallel execution with overhead costs