import hashlib
from typing import NamedTuple, Optional

from .serdes import WhitelistMap, serialize_value


def create_snapshot_id(snapshot: NamedTuple, whitelist_map: Optional[WhitelistMap] = None) -> str:
    kwargs = dict(whitelist_map=whitelist_map) if whitelist_map else {}
    json_rep = serialize_value(snapshot, **kwargs)
    return hash_str(json_rep)


def hash_str(in_str: str) -> str:
    m = hashlib.sha1()  # so that hexdigest is 40, not 64 bytes
    m.update(in_str.encode("utf-8"))
    return m.hexdigest()


def serialize_pp(value: NamedTuple) -> str:
    """Serialize and pretty print."""
    return serialize_value(value, indent=2, separators=(",", ": "))
