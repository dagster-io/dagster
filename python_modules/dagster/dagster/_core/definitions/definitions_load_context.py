from typing import TYPE_CHECKING, Literal, Optional

from dagster._record import record

if TYPE_CHECKING:
    from dagster._core.definitions.repository_definition import RepositoryLoadData

DefinitionsLoadType = Literal[
    "code_server", "step_worker", "run_worker", "step_launcher_external_step", "cli"
]


@record(checked=False)
class DefinitionsLoadContext:
    """Holds data that's made available to Definitions-loading code when a DefinitionsLoader is
    invoked.

    User construction of this object is not supported.
    """

    load_type: Optional[DefinitionsLoadType]
    repository_load_data: Optional["RepositoryLoadData"]

    @staticmethod
    def empty() -> "DefinitionsLoadContext":
        return DefinitionsLoadContext(load_type=None, repository_load_data=None)
