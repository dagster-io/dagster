import re
import warnings
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Dict, Mapping, Optional, Sequence, Tuple, Union

import dagster._seven as seven
from dagster import _check as check
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.storage.tags import check_reserved_tags

if TYPE_CHECKING:
    from dagster._core.execution.plan.step import ExecutionStep
    from dagster._core.storage.dagster_run import DagsterRun


class TagConcurrencyLimitsCounter:
    """Helper object that keeps track of when the tag concurrency limits are met."""

    _key_limits: Dict[str, int]
    _key_value_limits: Dict[Tuple[str, str], int]
    _unique_value_limits: Dict[str, int]
    _key_counts: Dict[str, int]
    _key_value_counts: Dict[Tuple[str, str], int]
    _unique_value_counts: Dict[Tuple[str, str], int]

    def __init__(
        self,
        tag_concurrency_limits: Sequence[Mapping[str, Any]],
        in_progress_tagged_items: Sequence[Union["DagsterRun", "ExecutionStep"]],
    ):
        check.opt_list_param(tag_concurrency_limits, "tag_concurrency_limits", of_type=dict)
        check.list_param(in_progress_tagged_items, "in_progress_tagged_items")

        self._key_limits = {}
        self._key_value_limits = {}
        self._unique_value_limits = {}

        for tag_limit in tag_concurrency_limits:
            key = tag_limit["key"]
            value = tag_limit.get("value")
            limit = tag_limit["limit"]

            if isinstance(value, str):
                self._key_value_limits[(key, value)] = limit
            elif not value or not value["applyLimitPerUniqueValue"]:
                self._key_limits[key] = limit
            else:
                self._unique_value_limits[key] = limit

        self._key_counts = defaultdict(lambda: 0)
        self._key_value_counts = defaultdict(lambda: 0)
        self._unique_value_counts = defaultdict(lambda: 0)

        # initialize counters based on current in progress item
        for item in in_progress_tagged_items:
            self.update_counters_with_launched_item(item)

    def is_blocked(self, item: Union["DagsterRun", "ExecutionStep"]) -> bool:
        """True if there are in progress item which are blocking this item based on tag limits."""
        for key, value in item.tags.items():
            if key in self._key_limits and self._key_counts[key] >= self._key_limits[key]:
                return True

            tag_tuple = (key, value)
            if (
                tag_tuple in self._key_value_limits
                and self._key_value_counts[tag_tuple] >= self._key_value_limits[tag_tuple]
            ):
                return True

            if (
                key in self._unique_value_limits
                and self._unique_value_counts[tag_tuple] >= self._unique_value_limits[key]
            ):
                return True

        return False

    def update_counters_with_launched_item(
        self, item: Union["DagsterRun", "ExecutionStep"]
    ) -> None:
        """Add a new in progress item to the counters."""
        for key, value in item.tags.items():
            if key in self._key_limits:
                self._key_counts[key] += 1

            tag_tuple = (key, value)
            if tag_tuple in self._key_value_limits:
                self._key_value_counts[tag_tuple] += 1

            if key in self._unique_value_limits:
                self._unique_value_counts[tag_tuple] += 1


def get_boolean_tag_value(tag_value: Optional[str], default_value: bool = False) -> bool:
    if tag_value is None:
        return default_value

    return tag_value.lower() not in {"false", "none", "0", ""}


# ########################
# ##### NORMALIZATION
# ########################

# There are two variants of tag normalization:
#
# 1. Legacy. Uses `normalize_tags`. Accepts a wide range of string keys and JSON-serializable values.
# 2. Strict. Uses `validate_tags_strict`. Accepts a restricted character set for string keys and
#    only accepts strings values.
#
# Legacy "tags" normalization supports an older vision of tags where potentially large values could
# be stored in tags to configure runs. It also supports (but issues a warning for) non-standard
# characters in tag keys like "&". We want to move away from this, but we still need to support it
# for backcompat.
#
# Strict "tags" normalization supports the new vision of tags where they are short string labels
# used for filtering and grouping in the UI. New tags arguments should generally use this
# normalization.


def normalize_tags(
    tags: Optional[Mapping[str, Any]],
    allow_reserved_tags: bool = True,
    warning_stacklevel: int = 4,
) -> Mapping[str, str]:
    """Normalizes JSON-object tags into string tags and warns on deprecated tags.

    New tags properties should _not_ use this function, because it doesn't hard error on tags that
    are no longer supported.
    """
    valid_tags: Dict[str, str] = {}
    invalid_tag_keys = []
    for key, value in check.opt_mapping_param(tags, "tags", key_type=str).items():
        if not isinstance(value, str):
            valid = False
            err_reason = f'Could not JSON encode value "{value}"'
            str_val = None
            try:
                str_val = seven.json.dumps(value)
                err_reason = f'JSON encoding "{str_val}" of value "{value}" is not equivalent to original value'

                valid = seven.json.loads(str_val) == value
            except Exception:
                pass

            if not valid:
                raise DagsterInvalidDefinitionError(
                    f'Invalid value for tag "{key}", {err_reason}. Tag values must be strings '
                    "or meet the constraint that json.loads(json.dumps(value)) == value."
                )

            valid_tags[key] = str_val  # type: ignore  # (possible none)
        else:
            valid_tags[key] = value

        if not is_valid_definition_tag_key(key):
            invalid_tag_keys.append(key)

    if invalid_tag_keys:
        invalid_tag_keys_sample = invalid_tag_keys[: min(5, len(invalid_tag_keys))]
        warnings.warn(
            f"Non-compliant tag keys like {invalid_tag_keys_sample} are deprecated. {VALID_DEFINITION_TAG_KEY_EXPLANATION}",
            category=DeprecationWarning,
            stacklevel=warning_stacklevel,
        )

    if not allow_reserved_tags:
        check_reserved_tags(valid_tags)

    return valid_tags


def validate_tag_strict(key: str, value: str) -> None:
    if not isinstance(key, str):
        raise DagsterInvalidDefinitionError("Tag keys must be strings")
    elif not isinstance(value, str):
        raise DagsterInvalidDefinitionError("Tag values must be strings")
    elif not is_valid_definition_tag_key(key):
        raise DagsterInvalidDefinitionError(
            f"Invalid tag key: {key}. {VALID_DEFINITION_TAG_KEY_EXPLANATION}"
        )
    elif not is_valid_definition_tag_value(value):
        raise DagsterInvalidDefinitionError(
            f"Invalid tag value: {value}, for key: {key}. Allowed characters: alpha-numeric, '_', '-', '.'. "
            "Must have <= 63 characters."
        )


def validate_tags_strict(tags: Optional[Mapping[str, str]]) -> Optional[Mapping[str, str]]:
    if tags is None:
        return tags

    for key, value in tags.items():
        validate_tag_strict(key, value)

    return tags


# Inspired by allowed Kubernetes labels:
# https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/#syntax-and-character-set

# We allow in some cases for users to specify multi-level namespaces for tags,
# right now we only allow this for the `dagster/kind` namespace, which is how asset kinds are
# encoded under the hood.
VALID_NESTED_NAMESPACES_TAG_KEYS = r"dagster/kind/"
VALID_DEFINITION_TAG_KEY_REGEX_STR = (
    r"^([A-Za-z0-9_.-]{1,63}/|" + VALID_NESTED_NAMESPACES_TAG_KEYS + r")?[A-Za-z0-9_.-]{1,63}$"
)
VALID_DEFINITION_TAG_KEY_REGEX = re.compile(VALID_DEFINITION_TAG_KEY_REGEX_STR)
VALID_DEFINITION_TAG_KEY_EXPLANATION = (
    "Allowed characters: alpha-numeric, '_', '-', '.'. "
    "Tag keys can also contain a namespace section, separated by a '/'. Each section "
    "must have <= 63 characters."
)

VALID_DEFINITION_TAG_VALUE_REGEX_STR = r"^[A-Za-z0-9_.-]{0,63}$"
VALID_DEFINITION_TAG_VALUE_REGEX = re.compile(VALID_DEFINITION_TAG_VALUE_REGEX_STR)


def is_valid_definition_tag_key(key: str) -> bool:
    return bool(VALID_DEFINITION_TAG_KEY_REGEX.match(key))


def is_valid_definition_tag_value(key: str) -> bool:
    return bool(VALID_DEFINITION_TAG_VALUE_REGEX.match(key))
