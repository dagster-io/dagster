from dataclasses import dataclass
from typing import List

import cython

"""
Before using this run

```
pip install cython
cythonize -i object_profile_schema_cython.py
```

This will create a compiled object_profile_schema_cython.blahblah.so in this dir.

"""

@dataclass(frozen=True)
@cython.cclass
class UnderTest:
    "cython"
    name: str
    nick_names: List[str]
