# Shared serdes objects to be used for JSON IPC between dg and the dagster CLI.


from typing import Any

from dagster_shared.record import record
from dagster_shared.serdes import whitelist_for_serdes


@whitelist_for_serdes
@record
class DagsterCliCommand:
    name: list[str]  # path - "asset materialize"
    options: list[str]

    # things the command can do that might not neatly fit into a list of options
    capabilities: list[str]


@whitelist_for_serdes
@record
class DagsterCliCommandInvocation:
    name: list[str]  # path - "asset materialize"
    options: dict[str, Any]


@whitelist_for_serdes
@record
class DagsterCliSchema:
    commands: list[DagsterCliCommand]
    capabilities: list[str]


@whitelist_for_serdes
@record
class DagsterCliRequest:
    name: str
    kwargs: dict[str, Any]
