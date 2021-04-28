from typing import NamedTuple, Optional

from dagster import check
from dagster.utils.backcompat import experimental_class_warning


class RetryPolicy(
    NamedTuple(
        "_RetryPolicy",
        [
            ("max_retries", int),
            ("delay", Optional[check.Numeric]),
            # delay control must be declarative - can't run a user function from host process orchestrator
        ],
    ),
):
    """
    A declarative policy for when to request retries when an exception occurs during solid execution.

    Args:
        max_retries (int):
            The maximum number of retries to attempt. Defaults to 1.
        delay (Optional[Union[int,float]]):
            The time in seconds to wait between the retry being requested and the next attempt being started.

    """

    def __new__(cls, max_retries=1, delay=None):
        experimental_class_warning("RetryPolicy")
        return super().__new__(
            cls,
            max_retries=check.int_param(max_retries, "max_retries"),
            delay=check.opt_numeric_param(delay, "delay"),
        )
