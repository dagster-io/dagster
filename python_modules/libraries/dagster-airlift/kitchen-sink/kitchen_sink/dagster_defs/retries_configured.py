import requests
from dagster import AssetExecutionContext, asset
from dagster._core.storage.tags import (
    AUTO_RETRY_RUN_ID_TAG,
    MAX_RETRIES_TAG,
    PARENT_RUN_ID_TAG,
    RETRY_NUMBER_TAG,
    WILL_RETRY_TAG,
)
from dagster_airlift.in_airflow.base_asset_operator import build_dagster_run_execution_params
from dagster_airlift.in_airflow.gql_queries import TRIGGER_ASSETS_MUTATION


# Asset that simulates having run retries activated (so that we don't have to stand up non-sqlite-storage)
@asset
def succeeds_on_final_retry(context: AssetExecutionContext):
    if RETRY_NUMBER_TAG not in context.run_tags or int(context.run_tags[RETRY_NUMBER_TAG]) < 2:
        # Launch a run of the "next retry". We need to do it in a separate request;
        # launching the job within the same request will cause weird context behavior.
        current_retry = int(context.run_tags.get(RETRY_NUMBER_TAG, 0))
        response = requests.post(
            "http://localhost:3333/graphql",
            json={
                "query": TRIGGER_ASSETS_MUTATION,
                "variables": {
                    "executionParams": build_dagster_run_execution_params(
                        tags={
                            **context.run_tags,
                            RETRY_NUMBER_TAG: str(current_retry + 1),
                            PARENT_RUN_ID_TAG: context.run_id,
                            MAX_RETRIES_TAG: "3",
                        },
                        job_identifier=(
                            "kitchen_sink.dagster_defs.mapped_defs",
                            "__repository__",
                            "__ASSET_JOB",
                        ),
                        asset_key_paths=["succeeds_on_final_retry"],
                    )
                },
            },
            timeout=10,
        )
        context.log.info(f"Received response: {response.json()}")
        retry_run_id = response.json()["data"]["launchPipelineExecution"]["run"]["id"]
        # Add a tag (before the run fails) to indicate that the current run will be retried
        context.log.info(f"Adding tag {WILL_RETRY_TAG} to run {context.run_id}")
        context.instance.run_storage.add_run_tags(
            context.run_id, {WILL_RETRY_TAG: "true", AUTO_RETRY_RUN_ID_TAG: retry_run_id}
        )
        raise Exception("oops i failed")
    return None


@asset
def just_fails():
    raise Exception("I fail every time")
