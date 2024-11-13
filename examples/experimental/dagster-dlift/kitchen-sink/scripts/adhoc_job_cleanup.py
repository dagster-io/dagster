# ruff: noqa: T201
from dagster_dlift.utils import DAGSTER_ADHOC_PREFIX
from dlift_kitchen_sink.instance import get_environment_id, get_unscoped_client

client = get_unscoped_client()
count = 0
for job in client.list_jobs(environment_id=get_environment_id()):
    if job["name"].startswith(DAGSTER_ADHOC_PREFIX):
        client.destroy_job(job["id"])
        count += 1
        print(f"Deleted job {job['id']}")
print(f"Deleted {count} jobs.")
