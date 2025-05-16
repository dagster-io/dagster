from enum import Enum

SYSTEM_TAG_PREFIX = "dagster/"
HIDDEN_TAG_PREFIX = ".dagster/"

KIND_PREFIX = f"{SYSTEM_TAG_PREFIX}kind/"

REPOSITORY_LABEL_TAG = f"{HIDDEN_TAG_PREFIX}repository"

SCHEDULE_NAME_TAG = f"{SYSTEM_TAG_PREFIX}schedule_name"

SENSOR_NAME_TAG = f"{SYSTEM_TAG_PREFIX}sensor_name"

TICK_ID_TAG = f"{SYSTEM_TAG_PREFIX}tick"

BACKFILL_ID_TAG = f"{SYSTEM_TAG_PREFIX}backfill"

PARTITION_NAME_TAG = f"{SYSTEM_TAG_PREFIX}partition"

MULTIDIMENSIONAL_PARTITION_PREFIX = f"{PARTITION_NAME_TAG}/"
get_multidimensional_partition_tag = (
    lambda dimension_name: f"{MULTIDIMENSIONAL_PARTITION_PREFIX}{dimension_name}"
)
get_dimension_from_partition_tag = lambda tag: tag[len(MULTIDIMENSIONAL_PARTITION_PREFIX) :]

ASSET_PARTITION_RANGE_START_TAG = f"{SYSTEM_TAG_PREFIX}asset_partition_range_start"

ASSET_PARTITION_RANGE_END_TAG = f"{SYSTEM_TAG_PREFIX}asset_partition_range_end"

PARTITION_SET_TAG = f"{SYSTEM_TAG_PREFIX}partition_set"

PARENT_RUN_ID_TAG = f"{SYSTEM_TAG_PREFIX}parent_run_id"

PARENT_BACKFILL_ID_TAG = f"{SYSTEM_TAG_PREFIX}parent_backfill_id"

ROOT_RUN_ID_TAG = f"{SYSTEM_TAG_PREFIX}root_run_id"

ROOT_BACKFILL_ID_TAG = f"{SYSTEM_TAG_PREFIX}root_backfill_id"

RESUME_RETRY_TAG = f"{SYSTEM_TAG_PREFIX}is_resume_retry"

ASSET_RESUME_RETRY_TAG = f"{SYSTEM_TAG_PREFIX}is_asset_resume_retry"

STEP_SELECTION_TAG = f"{SYSTEM_TAG_PREFIX}step_selection"

OP_SELECTION_TAG = f"{SYSTEM_TAG_PREFIX}solid_selection"

GRPC_INFO_TAG = f"{HIDDEN_TAG_PREFIX}grpc_info"

SCHEDULED_EXECUTION_TIME_TAG = f"{HIDDEN_TAG_PREFIX}scheduled_execution_time"

RUN_KEY_TAG = f"{SYSTEM_TAG_PREFIX}run_key"

PRIORITY_TAG = f"{SYSTEM_TAG_PREFIX}priority"

DOCKER_IMAGE_TAG = f"{SYSTEM_TAG_PREFIX}image"

MAX_RETRIES_TAG = f"{SYSTEM_TAG_PREFIX}max_retries"
RETRY_NUMBER_TAG = f"{SYSTEM_TAG_PREFIX}retry_number"
RETRY_STRATEGY_TAG = f"{SYSTEM_TAG_PREFIX}retry_strategy"
RETRY_ON_ASSET_OR_OP_FAILURE_TAG = f"{SYSTEM_TAG_PREFIX}retry_on_asset_or_op_failure"

# This tag is used to indicate that the automatic retry daemon will launch a retry for this run
# If this tag is not on a run, it means the run did not fail or automatic retries is disabled.
WILL_RETRY_TAG = f"{SYSTEM_TAG_PREFIX}will_retry"
# This tag will be added by the automatic retry daemon once it launches a retry for the run. The
# value will be the run_id of the retry.
AUTO_RETRY_RUN_ID_TAG = f"{SYSTEM_TAG_PREFIX}auto_retry_run_id"

MAX_RUNTIME_SECONDS_TAG = f"{SYSTEM_TAG_PREFIX}max_runtime"

AUTO_MATERIALIZE_TAG = f"{SYSTEM_TAG_PREFIX}auto_materialize"
AUTOMATION_CONDITION_TAG = f"{SYSTEM_TAG_PREFIX}from_automation_condition"
ASSET_EVALUATION_ID_TAG = f"{SYSTEM_TAG_PREFIX}asset_evaluation_id"
AUTO_OBSERVE_TAG = f"{SYSTEM_TAG_PREFIX}auto_observe"


RUN_WORKER_ID_TAG = f"{HIDDEN_TAG_PREFIX}run_worker"
GLOBAL_CONCURRENCY_TAG = f"{SYSTEM_TAG_PREFIX}concurrency_key"

# This tag is used to tag runs and backfills with the email of the creator.
USER_TAG = "user"

# This tag is used to tag runless asset events reported via the UI with the email of the reporting user.
REPORTING_USER_TAG = f"{SYSTEM_TAG_PREFIX}reporting_user"

RUN_ISOLATION_TAG = f"{SYSTEM_TAG_PREFIX}isolation"

RUN_FAILURE_REASON_TAG = f"{SYSTEM_TAG_PREFIX}failure_reason"

# Support for the legacy compute kind tag will be removed in 1.9.0
LEGACY_COMPUTE_KIND_TAG = "kind"
COMPUTE_KIND_TAG = f"{SYSTEM_TAG_PREFIX}compute_kind"

USER_EDITABLE_SYSTEM_TAGS = [
    PRIORITY_TAG,
    MAX_RETRIES_TAG,
    RETRY_STRATEGY_TAG,
    MAX_RUNTIME_SECONDS_TAG,
    RUN_ISOLATION_TAG,
    RETRY_ON_ASSET_OR_OP_FAILURE_TAG,
]

# Supports for the public tag is deprecated
RUN_METRIC_TAGS = [
    f"{HIDDEN_TAG_PREFIX}run_metrics",
    f"{SYSTEM_TAG_PREFIX}run_metrics",
]

RUN_METRICS_POLLING_INTERVAL_TAG = f"{HIDDEN_TAG_PREFIX}run_metrics_polling_interval"
RUN_METRICS_PYTHON_RUNTIME_TAG = f"{HIDDEN_TAG_PREFIX}python_runtime_metrics"

BACKFILL_TAGS = {BACKFILL_ID_TAG, PARENT_BACKFILL_ID_TAG, ROOT_BACKFILL_ID_TAG}

POOL_TAG_PREFIX = f"{HIDDEN_TAG_PREFIX}pool/"

EXTERNAL_JOB_SOURCE_TAG_KEY = f"{SYSTEM_TAG_PREFIX}external_job_source"

EXTERNALLY_MANAGED_ASSETS_TAG = f"{SYSTEM_TAG_PREFIX}defer_asset_events"

TAGS_TO_MAYBE_OMIT_ON_RETRY = {
    *RUN_METRIC_TAGS,
    RUN_FAILURE_REASON_TAG,
    RETRY_NUMBER_TAG,
    RESUME_RETRY_TAG,
    WILL_RETRY_TAG,
    AUTO_RETRY_RUN_ID_TAG,
    *BACKFILL_TAGS,
}

TAGS_INCLUDE_IN_REMOTE_JOB_REF = {
    EXTERNAL_JOB_SOURCE_TAG_KEY,
}


class TagType(Enum):
    # Custom tag provided by a user
    USER_PROVIDED = "USER_PROVIDED"

    # Tags used by Dagster to manage execution that should be surfaced to users.
    SYSTEM = "SYSTEM"

    # Metadata used by Dagster for execution but isn't useful for users to see.
    # For example, metadata about the gRPC server that executed a run.
    HIDDEN = "HIDDEN"


def get_tag_type(tag):
    if tag.startswith(SYSTEM_TAG_PREFIX):
        return TagType.SYSTEM
    elif tag.startswith(HIDDEN_TAG_PREFIX):
        return TagType.HIDDEN
    else:
        return TagType.USER_PROVIDED
