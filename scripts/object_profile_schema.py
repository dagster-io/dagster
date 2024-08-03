from dataclasses import dataclass
from typing import List

import cython


@dataclass(frozen=True)
@cython.cclass
class UnderTest:
    name: str
    nick_names: List[str]
