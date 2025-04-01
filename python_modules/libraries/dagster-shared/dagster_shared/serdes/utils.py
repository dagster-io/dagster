import hashlib
from typing import Optional

from dagster_shared.serdes.serdes import PackableValue, WhitelistMap, serialize_value


def create_snapshot_id(
    snapshot: PackableValue, whitelist_map: Optional[WhitelistMap] = None
) -> str:
    kwargs = dict(whitelist_map=whitelist_map) if whitelist_map else {}
    json_rep = serialize_value(snapshot, **kwargs)
    return hash_str(json_rep)


def hash_str(in_str: str) -> str:
    # so that hexdigest is 40, not 64 bytes
    return hashlib.sha1(in_str.encode("utf-8")).hexdigest()


def serialize_pp(value: PackableValue) -> str:
    """Serialize and pretty print."""
    return serialize_value(value, indent=2, separators=(",", ": "))
