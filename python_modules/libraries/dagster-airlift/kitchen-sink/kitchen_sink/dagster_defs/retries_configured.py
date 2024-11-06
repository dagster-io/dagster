from dagster import AssetExecutionContext, asset, materialize
from dagster._core.storage.tags import MAX_RETRIES_TAG, PARENT_RUN_ID_TAG, RETRY_NUMBER_TAG


# Asset that simulates having run retries activated (so that we don't have to stand up non-sqlite-storage)
@asset
def succeeds_on_final_retry(context: AssetExecutionContext):
    if RETRY_NUMBER_TAG not in context.run_tags or int(context.run_tags[RETRY_NUMBER_TAG]) < 2:
        # Launch a run of the "next retry"
        current_retry = int(context.run_tags.get(RETRY_NUMBER_TAG, 0))
        materialize(
            [succeeds_on_final_retry],
            instance=context.instance,
            tags={
                **context.run_tags,
                RETRY_NUMBER_TAG: str(current_retry + 1),
                PARENT_RUN_ID_TAG: context.run_id,
                MAX_RETRIES_TAG: "3",
            },
        )
        raise Exception("oops i failed")
    return None


@asset
def just_fails():
    raise Exception("I fail every time")
