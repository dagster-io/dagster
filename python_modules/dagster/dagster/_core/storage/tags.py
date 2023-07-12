from enum import Enum

import dagster._check as check

SYSTEM_TAG_PREFIX = "dagster/"
HIDDEN_TAG_PREFIX = ".dagster/"

REPOSITORY_LABEL_TAG = f"{HIDDEN_TAG_PREFIX}repository"

SCHEDULE_NAME_TAG = f"{SYSTEM_TAG_PREFIX}schedule_name"

SENSOR_NAME_TAG = f"{SYSTEM_TAG_PREFIX}sensor_name"

BACKFILL_ID_TAG = f"{SYSTEM_TAG_PREFIX}backfill"

PARTITION_NAME_TAG = f"{SYSTEM_TAG_PREFIX}partition"

MULTIDIMENSIONAL_PARTITION_PREFIX = f"{PARTITION_NAME_TAG}/"
get_multidimensional_partition_tag = (
    lambda dimension_name: f"{MULTIDIMENSIONAL_PARTITION_PREFIX}{dimension_name}"
)
get_dimension_from_partition_tag = lambda tag: tag[len(MULTIDIMENSIONAL_PARTITION_PREFIX) :]

ASSET_PARTITION_RANGE_START_TAG = "{prefix}asset_partition_range_start".format(
    prefix=SYSTEM_TAG_PREFIX
)

ASSET_PARTITION_RANGE_END_TAG = f"{SYSTEM_TAG_PREFIX}asset_partition_range_end"

PARTITION_SET_TAG = f"{SYSTEM_TAG_PREFIX}partition_set"

PARENT_RUN_ID_TAG = f"{SYSTEM_TAG_PREFIX}parent_run_id"

ROOT_RUN_ID_TAG = f"{SYSTEM_TAG_PREFIX}root_run_id"

RESUME_RETRY_TAG = f"{SYSTEM_TAG_PREFIX}is_resume_retry"

MEMOIZED_RUN_TAG = f"{SYSTEM_TAG_PREFIX}is_memoized_run"

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

MAX_RUNTIME_SECONDS_TAG = f"{SYSTEM_TAG_PREFIX}max_runtime"

AUTO_MATERIALIZE_TAG = f"{SYSTEM_TAG_PREFIX}auto_materialize"
ASSET_EVALUATION_ID_TAG = f"{SYSTEM_TAG_PREFIX}asset_evaluation_id"
AUTO_OBSERVE_TAG = f"{SYSTEM_TAG_PREFIX}auto_observe"

USER_EDITABLE_SYSTEM_TAGS = [
    PRIORITY_TAG,
    MAX_RETRIES_TAG,
    RETRY_STRATEGY_TAG,
    MAX_RUNTIME_SECONDS_TAG,
]

RUN_WORKER_ID_TAG = f"{HIDDEN_TAG_PREFIX}run_worker"
GLOBAL_CONCURRENCY_TAG = f"{SYSTEM_TAG_PREFIX}concurrency_key"

# In cloud, we tag runs with the email of the user who triggered the run
# This is used to display the user in the UI
USER_TAG = "user"


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


def check_reserved_tags(tags):
    check.opt_dict_param(tags, "tags", key_type=str, value_type=str)

    for tag in tags.keys():
        if tag not in USER_EDITABLE_SYSTEM_TAGS:
            check.invariant(
                not tag.startswith(SYSTEM_TAG_PREFIX),
                desc=f"Attempted to set tag with reserved system prefix: {tag}",
            )
