import logging
import random
from collections import defaultdict
from collections.abc import Callable, Iterable
from itertools import zip_longest
from typing import TypeVar

from dagster._utils.error import (
    ExceptionInfo,
    SerializableErrorInfo,
    serializable_error_info_from_exc_info,
)

T = TypeVar("T")


def shuffled_round_robin_by_key(items: Iterable[T], key: Callable[[T], str]) -> list[T]:
    """Round-robin interleave items across groups defined by ``key``, shuffling within
    and across groups so no individual item or group is consistently penalized by its
    position in the input.

    Items are grouped by ``key``, the order of items within each group is shuffled,
    the order of the groups themselves is shuffled, and then groups are interleaved
    round-robin so no single group can monopolize the head of the result.

    Used by the schedule, sensor, and asset daemons to fan items across code locations,
    so a single code location with many instigators cannot consistently push instigators
    from other code locations to the back of the thread pool queue, and so that no
    individual instigator (e.g. one whose name sorts last alphabetically within its
    code location) is consistently the last to be considered.
    """
    groups: dict[str, list[T]] = defaultdict(list)
    for item in items:
        groups[key(item)].append(item)
    group_lists = list(groups.values())
    for group in group_lists:
        random.shuffle(group)
    random.shuffle(group_lists)
    return [item for tup in zip_longest(*group_lists) for item in tup if item is not None]


class DaemonErrorCapture:
    @staticmethod
    def default_process_exception(
        exc_info: ExceptionInfo,
        logger: logging.Logger,
        log_message: str,
    ) -> SerializableErrorInfo:
        error_info = serializable_error_info_from_exc_info(exc_info)
        logger.exception(log_message)
        return error_info

    # global behavior for how to handle unexpected exceptions
    process_exception = default_process_exception
