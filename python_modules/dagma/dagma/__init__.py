"""Public API for dagma"""

from .engine import execute_plan
from .resources import define_dagma_resource

__all__ = [
    'define_dagma_resource',
    'execute_plan',
]
