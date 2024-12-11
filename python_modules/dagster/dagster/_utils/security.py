import hashlib
import sys
from typing import Union


def non_secure_md5_hash_str(s: Union[bytes, bytearray, memoryview]) -> str:
    """Drop in replacement md5 hash function marking it for a non-security purpose."""
    # check python version, use usedforsecurity flag if possible.
    if sys.version_info[0] <= 3 and sys.version_info[1] <= 8:
        return hashlib.md5(s).hexdigest()
    else:
        return hashlib.md5(s, usedforsecurity=False).hexdigest()
