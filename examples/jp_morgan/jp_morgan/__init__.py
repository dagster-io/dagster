from dagster import repository

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
