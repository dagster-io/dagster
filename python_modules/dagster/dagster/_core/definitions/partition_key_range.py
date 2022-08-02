from typing import NamedTuple

from dagster._annotations import PublicAttr


class PartitionKeyRange(NamedTuple):
    # Inclusive on both sides
    start: PublicAttr[str]
    end: PublicAttr[str]
