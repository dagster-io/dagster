from dataclasses import dataclass

from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.definitions.result import ObserveResult


# alias
class AssetPartition(AssetKeyPartitionKey):
    ...


@dataclass(frozen=True)
class SchedulingResult:
    execute: bool
    override_versioning: bool


class RequestReaction:
    pass


class SchedulingPolicy:
    # what about resources?
    def schedule(self) -> SchedulingResult:
        ...

    def observe(self) -> ObserveResult:
        ...

    def react_to_downstream_request(self) -> RequestReaction:
        ...

    def react_to_upstream_request(self) -> RequestReaction:
        ...
