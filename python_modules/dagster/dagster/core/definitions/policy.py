from enum import Enum
from random import random
from typing import NamedTuple, Optional

import dagster._check as check
from dagster.core.errors import DagsterInvalidDefinitionError


class Backoff(Enum):
    """
    A modifier for delay as a function of attempt number.

    LINEAR: `attempt_num * delay`
    EXPONENTIAL: `((2 ^ attempt_num) - 1) * delay`
    """

    LINEAR = "LINEAR"
    EXPONENTIAL = "EXPONENTIAL"


class Jitter(Enum):
    """A randomizing modifier for delay, applied after backoff calculation.

    FULL: between 0 and the calculated delay based on backoff: `random() * backoff_delay`
    PLUS_MINUS: +/- the delay: `backoff_delay + ((2 * (random() * delay)) - delay)`
    """

    FULL = "FULL"
    PLUS_MINUS = "PLUS_MINUS"


class RetryPolicy(
    NamedTuple(
        "_RetryPolicy",
        [
            ("max_retries", int),
            ("delay", Optional[check.Numeric]),
            # declarative time modulation to allow calc witout running user function
            ("backoff", Optional[Backoff]),
            ("jitter", Optional[Jitter]),
        ],
    ),
):
    """
    A declarative policy for when to request retries when an exception occurs during op execution.

    Args:
        max_retries (int):
            The maximum number of retries to attempt. Defaults to 1.
        delay (Optional[Union[int,float]]):
            The time in seconds to wait between the retry being requested and the next attempt
            being started. This unit of time can be modulated as a function of attempt number
            with backoff and randomly with jitter.
        backoff (Optional[Backoff]):
            A modifier for delay as a function of retry attempt number.
        jitter (Optional[Jitter]):
            A randomizing modifier for delay, applied after backoff calculation.
    """

    def __new__(
        cls,
        max_retries: int = 1,
        delay: Optional[check.Numeric] = None,
        backoff: Optional[Backoff] = None,
        jitter: Optional[Jitter] = None,
    ):
        if backoff is not None and delay is None:
            raise DagsterInvalidDefinitionError(
                "Can not set jitter on RetryPolicy without also setting delay"
            )

        if jitter is not None and delay is None:
            raise DagsterInvalidDefinitionError(
                "Can not set backoff on RetryPolicy without also setting delay"
            )

        return super().__new__(
            cls,
            max_retries=check.int_param(max_retries, "max_retries"),
            delay=check.opt_numeric_param(delay, "delay"),
            backoff=check.opt_inst_param(backoff, "backoff", Backoff),
            jitter=check.opt_inst_param(jitter, "jitter", Jitter),
        )

    def calculate_delay(self, attempt_num: int) -> check.Numeric:
        return calculate_delay(
            attempt_num=attempt_num,
            backoff=self.backoff,
            jitter=self.jitter,
            base_delay=self.delay or 0,
        )


def calculate_delay(attempt_num, backoff, jitter, base_delay):
    if backoff is Backoff.EXPONENTIAL:
        calc_delay = ((2**attempt_num) - 1) * base_delay
    elif backoff is Backoff.LINEAR:
        calc_delay = base_delay * attempt_num
    elif backoff is None:
        calc_delay = base_delay
    else:
        check.assert_never(backoff)

    if jitter is Jitter.FULL:
        calc_delay = random() * calc_delay
    elif jitter is Jitter.PLUS_MINUS:
        calc_delay = calc_delay + ((2 * (random() * base_delay)) - base_delay)
    elif jitter is None:
        pass
    else:
        check.assert_never(jitter)

    return calc_delay
