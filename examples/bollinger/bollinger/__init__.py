import warnings

from dagster import ExperimentalWarning, repository

from . import lib
from .jobs import bollinger_analysis

warnings.filterwarnings("ignore", category=ExperimentalWarning)


@repository(name="bollinger")
def repo():
    return [
        bollinger_analysis,
    ]


__all__ = [
    "repo",
    "lib",
]
