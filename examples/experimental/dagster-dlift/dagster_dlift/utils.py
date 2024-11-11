DAGSTER_ADHOC_PREFIX = "DAGSTER_ADHOC_JOB__"


def get_job_name(environment_id: int, project_id: int) -> str:
    return f"{DAGSTER_ADHOC_PREFIX}{project_id}__{environment_id}"
