from dagster.utils.merger import deep_merge_dicts

SAMPLE_ACCOUNT_ID = 30000
SAMPLE_JOB_ID = 40000
SAMPLE_RUN_ID = 5000000

SAMPLE_API_PREFIX = f"https://cloud.getdbt.com/api/v2/accounts/{SAMPLE_ACCOUNT_ID}"


def sample_job_details():
    return {
        "status": {
            "code": 200,
            "is_success": True,
            "user_message": "Success!",
            "developer_message": "",
        },
        "data": {
            "execution": {"timeout_seconds": 0},
            "generate_docs": False,
            "run_generate_sources": False,
            "id": SAMPLE_JOB_ID,
            "account_id": SAMPLE_ACCOUNT_ID,
            "project_id": 50000,
            "environment_id": 47000,
            "name": "MyCoolJob",
            "dbt_version": None,
            "created_at": "2021-10-29T21:35:33.278228+00:00",
            "updated_at": "2021-11-01T22:47:48.056913+00:00",
            "execute_steps": ["dbt run"],
            "state": 1,
            "deferring_job_definition_id": None,
            "lifecycle_webhooks": False,
            "lifecycle_webhooks_url": None,
            "triggers": {
                "github_webhook": False,
                "git_provider_webhook": False,
                "custom_branch_only": False,
                "schedule": False,
            },
            "settings": {"threads": 4, "target_name": "default"},
            "schedule": {
                "cron": "0 * * * *",
                "date": {"type": "every_day"},
                "time": {"type": "every_hour", "interval": 1},
            },
            "is_deferrable": False,
            "generate_sources": False,
            "cron_humanized": "Every hour",
            "next_run": None,
            "next_run_humanized": None,
        },
    }


def sample_run_details(include_related=None, **kwargs):
    base_data = {
        "id": SAMPLE_RUN_ID,
        "trigger_id": 33000000,
        "account_id": SAMPLE_ACCOUNT_ID,
        "environment_id": 47000,
        "project_id": 50000,
        "job_definition_id": SAMPLE_JOB_ID,
        "status": 10,
        "dbt_version": "0.21.0",
        "git_branch": "master",
        "git_sha": "a32e8239326887421f1314ee0890e5174c8f644a",
        "status_message": None,
        "owner_thread_id": None,
        "executed_by_thread_id": "dbt-run-3000000-6v5pm",
        "deferring_run_id": None,
        "artifacts_saved": True,
        "artifact_s3_path": "prod/runs/3000000/artifacts/target",
        "has_docs_generated": False,
        "has_sources_generated": False,
        "notifications_sent": True,
        "blocked_by": [],
        "scribe_enabled": True,
        "created_at": "2021-11-01 22:47:48.501943+00:00",
        "updated_at": "2021-11-01 22:48:44.860334+00:00",
        "dequeued_at": "2021-11-01 22:48:22.880352+00:00",
        "started_at": "2021-11-01 22:48:28.595439+00:00",
        "finished_at": "2021-11-01 22:48:44.684263+00:00",
        "last_checked_at": None,
        "last_heartbeat_at": None,
        "should_start_at": "2021-11-01 22:47:48.501943+00:00",
        "trigger": None,
        "job": None,
        "environment": None,
        "run_steps": [],
        "status_humanized": "Success",
        "in_progress": False,
        "is_complete": True,
        "is_success": True,
        "is_error": False,
        "is_cancelled": False,
        "href": "https://cloud.getdbt.com/#/accounts/30000/projects/50000/runs/3000000/",
        "duration": "00:00:56",
        "queued_duration": "00:00:40",
        "run_duration": "00:00:16",
        "duration_humanized": "56 seconds",
        "queued_duration_humanized": "40 seconds",
        "run_duration_humanized": "16 seconds",
        "created_at_humanized": "26 minutes, 12 seconds ago",
        "finished_at_humanized": "25 minutes, 16 seconds ago",
        "job_id": SAMPLE_JOB_ID,
    }
    if include_related:
        if "trigger" in include_related:
            base_data["trigger"] = {
                "id": 33149624,
                "cause": "Triggered via Dagster",
                "job_definition_id": SAMPLE_JOB_ID,
                "git_branch": None,
                "git_sha": None,
                "github_pull_request_id": None,
                "gitlab_merge_request_id": None,
                "schema_override": None,
                "dbt_version_override": None,
                "threads_override": None,
                "target_name_override": None,
                "generate_docs_override": None,
                "timeout_seconds_override": None,
                "steps_override": None,
                "created_at": "2021-11-01 22:47:48.494450+00:00",
                "cause_humanized": "Triggered via Dagster",
                "job": None,
            }
        if "job" in include_related:
            base_data["job"] = {
                "execution": {"timeout_seconds": 0},
                "generate_docs": False,
                "run_generate_sources": False,
                "id": SAMPLE_JOB_ID,
                "account_id": SAMPLE_ACCOUNT_ID,
                "project_id": 50000,
                "environment_id": 47071,
                "name": "MyCoolJob",
                "dbt_version": None,
                "created_at": "2021-10-29T21:35:33.278228Z",
                "updated_at": "2021-11-01T23:03:20.887248Z",
                "execute_steps": ["dbt run"],
                "state": 1,
                "deferring_job_definition_id": None,
                "lifecycle_webhooks": False,
                "lifecycle_webhooks_url": None,
                "triggers": {
                    "github_webhook": False,
                    "git_provider_webhook": False,
                    "custom_branch_only": False,
                    "schedule": False,
                },
                "settings": {"threads": 4, "target_name": "default"},
            }
    return {
        "status": {
            "code": 200,
            "is_success": True,
            "user_message": "Success!",
            "developer_message": "",
        },
        "data": deep_merge_dicts(base_data, kwargs),
    }


def sample_list_artifacts():
    return {
        "status": {
            "code": 200,
            "is_success": True,
            "user_message": "Success!",
            "developer_message": "",
        },
        "data": [
            "compiled/my_new_project/models/example/my_first_dbt_model.sql",
            "compiled/my_new_project/models/example/my_second_dbt_model.sql",
            "manifest.json",
            "run/my_new_project/models/example/my_first_dbt_model.sql",
            "run/my_new_project/models/example/my_second_dbt_model.sql",
            "run_results.json",
        ],
    }


def sample_run_results():
    return {
        "metadata": {
            "dbt_schema_version": "https://schemas.getdbt.com/dbt/run-results/v3.json",
            "dbt_version": "0.21.0",
            "generated_at": "2021-11-01T22:48:44.212488Z",
            "invocation_id": "742f932b-3cd1-41b0-9e19-8ce6b39f6b41",
            "env": {
                "DBT_CLOUD_PROJECT_ID": "50000",
                "DBT_CLOUD_RUN_ID": "3000000",
                "DBT_CLOUD_JOB_ID": "40000",
                "DBT_CLOUD_RUN_REASON": "Triggered via Dagster",
                "DBT_CLOUD_RUN_REASON_CATEGORY": "other",
            },
        },
        "results": [
            {
                "status": "success",
                "timing": [
                    {
                        "name": "compile",
                        "started_at": "2021-11-01T22:48:42.325672Z",
                        "completed_at": "2021-11-01T22:48:42.329216Z",
                    },
                    {
                        "name": "execute",
                        "started_at": "2021-11-01T22:48:42.329430Z",
                        "completed_at": "2021-11-01T22:48:43.561620Z",
                    },
                ],
                "thread_id": "Thread-10",
                "execution_time": 1.3390405178070068,
                "adapter_response": {
                    "_message": "SUCCESS 1",
                    "code": "SUCCESS",
                    "rows_affected": 1,
                },
                "message": "SUCCESS 1",
                "failures": None,
                "unique_id": "model.my_new_project.my_first_dbt_model",
            },
            {
                "status": "success",
                "timing": [
                    {
                        "name": "compile",
                        "started_at": "2021-11-01T22:48:43.666997Z",
                        "completed_at": "2021-11-01T22:48:43.670584Z",
                    },
                    {
                        "name": "execute",
                        "started_at": "2021-11-01T22:48:43.670787Z",
                        "completed_at": "2021-11-01T22:48:44.133335Z",
                    },
                ],
                "thread_id": "Thread-12",
                "execution_time": 0.5428340435028076,
                "adapter_response": {
                    "_message": "SUCCESS 1",
                    "code": "SUCCESS",
                    "rows_affected": 1,
                },
                "message": "SUCCESS 1",
                "failures": None,
                "unique_id": "model.my_new_project.my_second_dbt_model",
            },
        ],
        "elapsed_time": 3.3942739963531494,
        "args": {
            "log_format": "default",
            "write_json": True,
            "use_experimental_parser": False,
            "profiles_dir": "/tmp/jobs/300000/.dbt",
            "profile": "user",
            "target": "default",
            "use_cache": True,
            "version_check": True,
            "which": "run",
            "rpc_method": "run",
        },
    }
