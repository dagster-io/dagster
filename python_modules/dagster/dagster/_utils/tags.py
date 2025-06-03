import re
import warnings
from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Optional, Union

import dagster_shared.seven as seven
from dagster_shared.utils import get_boolean_string_value

from dagster import _check as check
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.storage.tags import SYSTEM_TAG_PREFIX, USER_EDITABLE_SYSTEM_TAGS

if TYPE_CHECKING:
    from dagster._core.execution.plan.step import ExecutionStep
    from dagster._core.storage.dagster_run import DagsterRun


class TagConcurrencyLimitsCounter:
    """Helper object that keeps track of when the tag concurrency limits are met."""

    _key_limits: dict[str, int]
    _key_value_limits: dict[tuple[str, str], int]
    _unique_value_limits: dict[str, int]
    _key_counts: dict[str, int]
    _key_value_counts: dict[tuple[str, str], int]
    _unique_value_counts: dict[tuple[str, str], int]

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

    return get_boolean_string_value(tag_value)


# ########################
# ##### NORMALIZATION
# ########################

# Tag key constraints are inspired by allowed Kubernetes labels:
# https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/#syntax-and-character-set

# We allow in some cases for users to specify multi-level namespaces for tags,
# right now we only allow this for the `dagster/kind` namespace, which is how asset kinds are
# encoded under the hood.
VALID_NESTED_NAMESPACES_TAG_KEYS = r"dagster/kind/"
VALID_TAG_KEY_REGEX = re.compile(
    r"^([A-Za-z0-9_.-]{1,63}/|" + VALID_NESTED_NAMESPACES_TAG_KEYS + r")?[A-Za-z0-9_.-]{1,63}$"
)
VALID_TAG_KEY_EXPLANATION = (
    "Allowed characters: alpha-numeric, '_', '-', '.'. "
    "Tag keys can also contain a namespace section, separated by a '/'. Each section "
    "must have <= 63 characters."
)

VALID_STRICT_TAG_VALUE_REGEX = re.compile(r"^[A-Za-z0-9_.-]{0,63}$")


def normalize_tags(
    tags: Optional[Mapping[str, Any]],
    strict: bool = False,
    allow_private_system_tags: bool = True,
    warning_stacklevel: int = 4,
) -> Mapping[str, str]:
    """Normalizes key-value tags attached to definitions throughout Dagster.

    Tag normalization is complicated for backcompat reasons. In the past, tags were permitted to be
    arbitrary and potentially large JSON-serializable objects. This is inconsistent with the vision
    we have for tags going forward, which is as short string labels used for filtering and grouping
    in the UI.

    The `strict` flag controls whether to normalize/validate tags according to the new vision or the
    old. `strict` should be set whenever we are normalizing a tags parameter that is newly added. It
    should not be set if we are normalizing an older tags parameter for which we are maintaining old
    behavior.

    Args:
        strict (bool):
            If `strict=True`, we accept a restricted character set and impose length restrictions
            (<=63 characters) for string keys and values. Violations of these constraints raise
            errors. If `strict=False` then we run the same test but only warn for keys. Values are
            permitted to be any JSON-serializable object that is unaffected by JSON round-trip.
            Unserializable or round-trip-unequal values raise errors. Values are normalized to the
            JSON string representation in the return value.
        allow_private_system_tags (bool):
            Whether to allow non-whitelisted tags that start with the system tag prefix. This should
            be set to False whenever we are dealing with exclusively user-provided tags.
        warning_stacklevel (int):
            The stacklevel to use for warnings. This should be set to the calling function's
            stacklevel.

    Returns:
        Mapping[str, str]: A dictionary of normalized tags.
    """
    normalized_tags: dict[str, str] = {}
    invalid_tag_keys = []

    for key, value in check.opt_mapping_param(tags, "tags", key_type=str).items():
        # Validate the key
        if not isinstance(key, str):
            raise DagsterInvalidDefinitionError("Tag keys must be strings")
        elif (not allow_private_system_tags) and is_private_system_tag_key(key):
            raise DagsterInvalidDefinitionError(
                f"Attempted to set tag with reserved system prefix: {key}"
            )
        elif not is_valid_tag_key(key):
            invalid_tag_keys.append(key)

        # Normalize the value
        if not isinstance(value, str):
            if strict:
                raise DagsterInvalidDefinitionError(
                    f"Tag values must be strings, got type {type(value)} at key {key}."
                )
            else:
                normalized_tags[key] = _normalize_value(value, key)
        else:
            if strict and not is_valid_strict_tag_value(value):
                raise DagsterInvalidDefinitionError(
                    f"Invalid tag value: {value}, for key: {key}. Allowed characters: alpha-numeric, '_', '-', '.'. "
                    "Must have <= 63 characters."
                )
            normalized_tags[key] = value

    # Issue errors (strict=True) or warnings (strict=False) for any invalid tag keys that are too
    # long or contain invalid characters.
    if invalid_tag_keys:
        invalid_tag_keys_sample = invalid_tag_keys[: min(5, len(invalid_tag_keys))]
        if strict:
            raise DagsterInvalidDefinitionError(
                f"Found invalid tag keys: {invalid_tag_keys_sample}. {VALID_TAG_KEY_EXPLANATION}"
            )
        else:
            warnings.warn(
                f"Non-compliant tag keys like {invalid_tag_keys_sample} are deprecated. {VALID_TAG_KEY_EXPLANATION}",
                category=DeprecationWarning,
                stacklevel=warning_stacklevel,
            )

    return normalized_tags


def _normalize_value(value: Any, key: str) -> str:
    error = None
    try:
        serialized_value = seven.json.dumps(value)
    except TypeError:
        error = 'Could not JSON encode value "{value}"'
    if not error and not seven.json.loads(serialized_value) == value:  # pyright: ignore[reportPossiblyUnboundVariable]
        error = f'JSON encoding "{serialized_value}" of value "{value}" is not equivalent to original value'  # pyright: ignore[reportPossiblyUnboundVariable]
    if error:
        raise DagsterInvalidDefinitionError(
            f'Invalid value for tag "{key}", {error}. Tag values must be strings '
            "or meet the constraint that json.loads(json.dumps(value)) == value."
        )
    return serialized_value  # pyright: ignore[reportPossiblyUnboundVariable]


def is_private_system_tag_key(tag) -> bool:
    return tag.startswith(SYSTEM_TAG_PREFIX) and tag not in USER_EDITABLE_SYSTEM_TAGS


def is_valid_tag_key(key: str) -> bool:
    return bool(VALID_TAG_KEY_REGEX.match(key))


def is_valid_strict_tag_value(key: str) -> bool:
    return bool(VALID_STRICT_TAG_VALUE_REGEX.match(key))
