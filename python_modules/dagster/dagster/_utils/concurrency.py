from enum import Enum


class ConcurrencyState(Enum):
    BLOCKED = "BLOCKED"
    CLAIMED = "CLAIMED"
