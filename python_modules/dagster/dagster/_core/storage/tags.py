from enum import Enum
from typing import Sequence
from typing_extensions import Final

import dagster._check as check

SYSTEM_TAG_PREFIX: Final[str] = "dagster/"
HIDDEN_TAG_PREFIX: Final[str] = ".dagster/"

REPOSITORY_LABEL_TAG: Final[str] = f"{HIDDEN_TAG_PREFIX}repository"

SCHEDULE_NAME_TAG: Final[str] = f"{SYSTEM_TAG_PREFIX}schedule_name"

SENSOR_NAME_TAG: Final[str] = f"{SYSTEM_TAG_PREFIX}sensor_name"

BACKFILL_ID_TAG: Final[str] = f"{SYSTEM_TAG_PREFIX}backfill"

PARTITION_NAME_TAG: Final[str] = f"{SYSTEM_TAG_PREFIX}partition"

MULTIDIMENSIONAL_PARTITION_PREFIX: Final[str] = f"{PARTITION_NAME_TAG}/"
get_multidimensional_partition_tag = (
    lambda dimension_name: f"{MULTIDIMENSIONAL_PARTITION_PREFIX}{dimension_name}"
)
get_dimension_from_partition_tag = lambda tag: tag[len(MULTIDIMENSIONAL_PARTITION_PREFIX) :]

ASSET_PARTITION_RANGE_START_TAG: Final[str] = f"{SYSTEM_TAG_PREFIX}asset_partition_range_start"

ASSET_PARTITION_RANGE_END_TAG: Final[str] = f"{SYSTEM_TAG_PREFIX}asset_partition_range_end"

CODE_VERSION_TAG: Final[str] = f"{SYSTEM_TAG_PREFIX}code_version"

INPUT_EVENT_POINTER_TAG_PREFIX: Final[str] = f"{SYSTEM_TAG_PREFIX}input_event_pointer"

INPUT_LOGICAL_VERSION_TAG_PREFIX: Final[str] = f"{SYSTEM_TAG_PREFIX}input_logical_version"

LOGICAL_VERSION_TAG: Final[str] = f"{SYSTEM_TAG_PREFIX}logical_version"

PARTITION_SET_TAG: Final[str] = f"{SYSTEM_TAG_PREFIX}partition_set"

PARENT_RUN_ID_TAG: Final[str] = f"{SYSTEM_TAG_PREFIX}parent_run_id"

ROOT_RUN_ID_TAG: Final[str] = f"{SYSTEM_TAG_PREFIX}root_run_id"

RESUME_RETRY_TAG: Final[str] = f"{SYSTEM_TAG_PREFIX}is_resume_retry"

MEMOIZED_RUN_TAG: Final[str] = f"{SYSTEM_TAG_PREFIX}is_memoized_run"

STEP_SELECTION_TAG: Final[str] = f"{SYSTEM_TAG_PREFIX}step_selection"

SOLID_SELECTION_TAG: Final[str] = f"{SYSTEM_TAG_PREFIX}solid_selection"

PRESET_NAME_TAG: Final[str] = f"{SYSTEM_TAG_PREFIX}preset_name"

GRPC_INFO_TAG: Final[str] = f"{HIDDEN_TAG_PREFIX}grpc_info"

SCHEDULED_EXECUTION_TIME_TAG: Final[str] = f"{HIDDEN_TAG_PREFIX}scheduled_execution_time"

RUN_KEY_TAG: Final[str] = f"{SYSTEM_TAG_PREFIX}run_key"

PRIORITY_TAG: Final[str] = f"{SYSTEM_TAG_PREFIX}priority"

DOCKER_IMAGE_TAG: Final[str] = f"{SYSTEM_TAG_PREFIX}image"

MAX_RETRIES_TAG: Final[str] = f"{SYSTEM_TAG_PREFIX}max_retries"
RETRY_NUMBER_TAG: Final[str] = f"{SYSTEM_TAG_PREFIX}retry_number"
RETRY_STRATEGY_TAG: Final[str] = f"{SYSTEM_TAG_PREFIX}retry_strategy"

USER_EDITABLE_SYSTEM_TAGS: Final[Sequence[str]] = [PRIORITY_TAG, MAX_RETRIES_TAG, RETRY_STRATEGY_TAG]


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
        if not tag in USER_EDITABLE_SYSTEM_TAGS:
            check.invariant(
                not tag.startswith(SYSTEM_TAG_PREFIX),
                desc="Attempted to set tag with reserved system prefix: {tag}".format(tag=tag),
            )
