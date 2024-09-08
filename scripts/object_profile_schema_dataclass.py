from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class UnderTest:
    "dataclass"
    name: str
    nick_names: List[str]
