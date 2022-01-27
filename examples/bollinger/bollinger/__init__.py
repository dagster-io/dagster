import warnings

from dagster import repository, ExperimentalWarning
warnings.filterwarnings("ignore", category=ExperimentalWarning)

from .jobs import bollinger_sda, bollinger_vanilla
from . import lib

@repository
def repo():
    return [
        bollinger_sda,
        bollinger_vanilla,
    ]

__all__ = [
    'repo',
    'lib',
]
