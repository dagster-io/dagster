from dagster import AssetKey
from dagster._core.storage.tags import COMPUTE_KIND_TAG
from dagster._utils.merger import deep_merge_dicts

SAMPLE_PROJECT_ID = 35000
SAMPLE_JOB_ID = 40000
SAMPLE_RUN_ID = 5000000

DBT_CLOUD_API_TOKEN = "abc"
DBT_CLOUD_ACCOUNT_ID = 30000
DBT_CLOUD_US_HOST = "https://cloud.getdbt.com/"
DBT_CLOUD_EMEA_HOST = "https://emea.dbt.com/"

SAMPLE_API_PREFIX = f"{DBT_CLOUD_US_HOST}api/v2/accounts/{DBT_CLOUD_ACCOUNT_ID}"
SAMPLE_API_V3_PREFIX = f"{DBT_CLOUD_US_HOST}api/v3/accounts/{DBT_CLOUD_ACCOUNT_ID}"

SAMPLE_EMEA_API_PREFIX = f"{DBT_CLOUD_EMEA_HOST}api/v2/accounts/{DBT_CLOUD_ACCOUNT_ID}"
SAMPLE_EMEA_API_V3_PREFIX = f"{DBT_CLOUD_EMEA_HOST}api/v3/accounts/{DBT_CLOUD_ACCOUNT_ID}"


def job_details_data(job_id: int):
    return {
        "execution": {"timeout_seconds": 0},
        "generate_docs": False,
        "run_generate_sources": False,
        "id": job_id,
        "account_id": DBT_CLOUD_ACCOUNT_ID,
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
    }


def sample_list_job_details():
    return {
        "status": {
            "code": 200,
            "is_success": True,
            "user_message": "Success!",
            "developer_message": "",
        },
        "data": [job_details_data(job_id=SAMPLE_JOB_ID)],
    }


def sample_job_details():
    return {
        "status": {
            "code": 200,
            "is_success": True,
            "user_message": "Success!",
            "developer_message": "",
        },
        "data": [job_details_data(job_id=SAMPLE_JOB_ID)],
    }


def sample_runs_details(include_related=None, **kwargs):
    runs = [sample_run_details(include_related, **kwargs) for i in range(100)]
    if include_related and "environment" in include_related:
        for i, run in enumerate(runs):
            run["environment"] = {
                "dbt_project_subdirectory": None,
                "project_id": 50000,
                "id": 47000,
                "account_id": DBT_CLOUD_ACCOUNT_ID,
                "connection_id": 56000,
                "repository_id": 58000,
                "credentials_id": 52000,
                "created_by_id": None,
                "name": "dbt-environment",
                "use_custom_branch": False,
                "custom_branch": None,
                "dbt_version": "0.21.0",
                "supports_docs": False,
                "state": 10,
            }
            runs[i] = deep_merge_dicts(run, kwargs)
    return {
        "status": {
            "code": 200,
            "is_success": True,
            "user_message": "Success!",
            "developer_message": "",
        },
        "data": runs,
    }


def sample_run_details(include_related=None, **kwargs):
    base_data = {
        "id": SAMPLE_RUN_ID,
        "trigger_id": 33000000,
        "account_id": DBT_CLOUD_ACCOUNT_ID,
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
        "job": {"triggers": {"schedule": True}},
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
                "account_id": DBT_CLOUD_ACCOUNT_ID,
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


def sample_get_environment_variables(environment_variable_id: int, name: str, value: str):
    return {
        "status": {
            "code": 200,
            "is_success": True,
            "user_message": "Success!",
            "developer_message": "",
        },
        "data": {
            name: {
                "project": {"id": 1, "value": "-1"},
                "environment": {"id": 2, "value": "-1"},
                "job": {"id": environment_variable_id, "value": value},
            },
        },
    }


def sample_set_environment_variable(environment_variable_id: int, name: str, value: str):
    return {
        "status": {
            "code": 200,
            "is_success": True,
            "user_message": "Success!",
            "developer_message": "",
        },
        "data": {
            "account_id": DBT_CLOUD_ACCOUNT_ID,
            "project_id": SAMPLE_PROJECT_ID,
            "name": name,
            "type": "job",
            "state": 1,
            "user_id": None,
            "environment_id": None,
            "job_definition_id": SAMPLE_JOB_ID,
            "environment": None,
            "display_value": value,
            "id": environment_variable_id,
            "created_at": "2023-01-01 10:00:00.000000+00:00",
            "updated_at": "2023-01-02 10:00:00.000000+00:00",
        },
    }


def assert_assets_match_project(
    dbt_assets, include_seeds_and_snapshots: bool = True, prefix=None, has_non_argument_deps=False
):
    if prefix is None:
        prefix = []
    elif isinstance(prefix, str):
        prefix = [prefix]

    assert len(dbt_assets) == 1
    assets_op = dbt_assets[0].op
    assert assets_op.tags == {COMPUTE_KIND_TAG: "dbt"}

    # this is the set of keys which are "true" inputs to the op, rather than placeholder inputs
    # which will not be used if this op is run without subsetting
    non_subset_input_keys = set(dbt_assets[0].keys_by_input_name.values()) - dbt_assets[0].keys
    assert len(non_subset_input_keys) == bool(has_non_argument_deps)

    def_outputs = sorted(set(assets_op.output_dict.keys()))
    expected_outputs = sorted(
        [
            "cold_schema__sort_cold_cereals_by_calories",
            "sort_by_calories",
            "sort_hot_cereals_by_calories",
            "subdir_schema__least_caloric",
        ]
        + (
            [
                "seed_dagster_dbt_test_project_cereals",
                "snapshot_dagster_dbt_test_project_orders_snapshot",
            ]
            if include_seeds_and_snapshots
            else []
        )
    )
    assert def_outputs == expected_outputs, f"{def_outputs} != {expected_outputs}"
    for asset_name in [
        "subdir_schema/least_caloric",
        "sort_hot_cereals_by_calories",
        "cold_schema/sort_cold_cereals_by_calories",
    ]:
        asset_key = AssetKey(prefix + asset_name.split("/"))
        assert dbt_assets[0].asset_deps[asset_key] == {AssetKey(prefix + ["sort_by_calories"])}

    for asset_key, group_name in dbt_assets[0].group_names_by_key.items():
        assert group_name == "default", f'{asset_key} group {group_name} != "default"'

    assert AssetKey(prefix + ["sort_by_calories"]) in dbt_assets[0].keys
    sort_by_calories_deps = dbt_assets[0].asset_deps[AssetKey(prefix + ["sort_by_calories"])]
    assert sort_by_calories_deps == {AssetKey(prefix + ["cereals"])}, sort_by_calories_deps
