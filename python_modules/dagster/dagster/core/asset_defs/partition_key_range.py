from typing import NamedTuple


class PartitionKeyRange(NamedTuple):
    # Inclusive on both sides
    start: str
    end: str
