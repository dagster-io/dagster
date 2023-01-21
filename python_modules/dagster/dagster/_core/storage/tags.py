from enum import Enum

import dagster._check as check

SYSTEM_TAG_PREFIX = "dagster/"
HIDDEN_TAG_PREFIX = ".dagster/"

REPOSITORY_LABEL_TAG = f"{HIDDEN_TAG_PREFIX}repository"

SCHEDULE_NAME_TAG = "{prefix}schedule_name".format(prefix=SYSTEM_TAG_PREFIX)

SENSOR_NAME_TAG = "{prefix}sensor_name".format(prefix=SYSTEM_TAG_PREFIX)

BACKFILL_ID_TAG = "{prefix}backfill".format(prefix=SYSTEM_TAG_PREFIX)

PARTITION_NAME_TAG = "{prefix}partition".format(prefix=SYSTEM_TAG_PREFIX)

MULTIDIMENSIONAL_PARTITION_PREFIX = f"{PARTITION_NAME_TAG}/"
get_multidimensional_partition_tag = (
    lambda dimension_name: f"{MULTIDIMENSIONAL_PARTITION_PREFIX}{dimension_name}"
)
get_dimension_from_partition_tag = lambda tag: tag[len(MULTIDIMENSIONAL_PARTITION_PREFIX) :]

ASSET_PARTITION_RANGE_START_TAG = "{prefix}asset_partition_range_start".format(
    prefix=SYSTEM_TAG_PREFIX
)

ASSET_PARTITION_RANGE_END_TAG = "{prefix}asset_partition_range_end".format(prefix=SYSTEM_TAG_PREFIX)

PARTITION_SET_TAG = "{prefix}partition_set".format(prefix=SYSTEM_TAG_PREFIX)

PARENT_RUN_ID_TAG = "{prefix}parent_run_id".format(prefix=SYSTEM_TAG_PREFIX)

ROOT_RUN_ID_TAG = "{prefix}root_run_id".format(prefix=SYSTEM_TAG_PREFIX)

RESUME_RETRY_TAG = "{prefix}is_resume_retry".format(prefix=SYSTEM_TAG_PREFIX)

MEMOIZED_RUN_TAG = "{prefix}is_memoized_run".format(prefix=SYSTEM_TAG_PREFIX)

STEP_SELECTION_TAG = "{prefix}step_selection".format(prefix=SYSTEM_TAG_PREFIX)

SOLID_SELECTION_TAG = "{prefix}solid_selection".format(prefix=SYSTEM_TAG_PREFIX)

PRESET_NAME_TAG = "{prefix}preset_name".format(prefix=SYSTEM_TAG_PREFIX)

GRPC_INFO_TAG = "{prefix}grpc_info".format(prefix=HIDDEN_TAG_PREFIX)

SCHEDULED_EXECUTION_TIME_TAG = "{prefix}scheduled_execution_time".format(prefix=HIDDEN_TAG_PREFIX)

RUN_KEY_TAG = "{prefix}run_key".format(prefix=SYSTEM_TAG_PREFIX)

PRIORITY_TAG = "{prefix}priority".format(prefix=SYSTEM_TAG_PREFIX)

DOCKER_IMAGE_TAG = "{prefix}image".format(prefix=SYSTEM_TAG_PREFIX)

MAX_RETRIES_TAG = "{prefix}max_retries".format(prefix=SYSTEM_TAG_PREFIX)
RETRY_NUMBER_TAG = "{prefix}retry_number".format(prefix=SYSTEM_TAG_PREFIX)
RETRY_STRATEGY_TAG = "{prefix}retry_strategy".format(prefix=SYSTEM_TAG_PREFIX)

USER_EDITABLE_SYSTEM_TAGS = [PRIORITY_TAG, MAX_RETRIES_TAG, RETRY_STRATEGY_TAG]


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
                desc="Attempted to set tag with reserved system prefix: {tag}".format(tag=tag),
            )
