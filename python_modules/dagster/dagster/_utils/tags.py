from collections import defaultdict
from typing import TYPE_CHECKING, Any, Dict, Mapping, Sequence, Tuple, Union

from dagster import _check as check

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
