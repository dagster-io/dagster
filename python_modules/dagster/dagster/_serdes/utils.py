import hashlib
from typing import NamedTuple

from .serdes import serialize_dagster_namedtuple


def create_snapshot_id(snapshot: NamedTuple) -> str:
    json_rep = serialize_dagster_namedtuple(snapshot)
    return hash_str(json_rep)


def hash_str(in_str: str) -> str:
    m = hashlib.sha1()  # so that hexdigest is 40, not 64 bytes
    m.update(in_str.encode("utf-8"))
    return m.hexdigest()


def serialize_pp(value: NamedTuple) -> str:
    """Serialize and pretty print."""
    return serialize_dagster_namedtuple(value, indent=2, separators=(",", ": "))
