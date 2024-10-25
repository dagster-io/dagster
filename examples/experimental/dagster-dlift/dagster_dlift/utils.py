def get_job_name(environment_id: int, project_id: int) -> str:
    return f"DAGSTER_ADHOC_JOB__{project_id}__{environment_id}"
