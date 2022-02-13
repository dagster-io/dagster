import warnings

from dagster import repository, ExperimentalWarning

warnings.filterwarnings("ignore", category=ExperimentalWarning)

from .jobs import bollinger_analysis
from . import lib


@repository(name="bollinger")
def repo():
    return [
        bollinger_analysis,
    ]


__all__ = [
    "repo",
    "lib",
]
