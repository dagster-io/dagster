import warnings

from dagster import repository, ExperimentalWarning

warnings.filterwarnings("ignore", category=ExperimentalWarning)

from .jobs import bollinger_op, bollinger_sda, bollinger_sda_inline, bollinger_sda_inline_basic
from . import lib


@repository(name="bollinger")
def repo():
    # NOTE: Only one variant of `bollinger_sda*` can be defined in the repo at once, because assets
    # are uniquely identified by their name, and all bollinger_sda jobs share the same asset names.
    return [
        # bollinger_sda_inline,
        # bollinger_sda_inline_basic,
        bollinger_sda,
        bollinger_op,
    ]


__all__ = [
    "repo",
    "lib",
]
