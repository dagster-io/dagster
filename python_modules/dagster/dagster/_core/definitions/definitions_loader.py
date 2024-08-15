from typing import Callable

from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.definitions_load_context import DefinitionsLoadContext
from dagster._record import record


@record
class DefinitionsLoader:
    """An object that can be invoked to load a set of definitions."""

    load_fn: Callable[[DefinitionsLoadContext], Definitions]
