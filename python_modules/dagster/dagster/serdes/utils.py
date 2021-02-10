import hashlib
from typing import NamedTuple

from .serdes import serialize_dagster_namedtuple


def create_snapshot_id(snapshot: NamedTuple) -> str:
    json_rep = serialize_dagster_namedtuple(snapshot)
    m = hashlib.sha1()  # so that hexdigest is 40, not 64 bytes
    m.update(json_rep.encode("utf-8"))
    return m.hexdigest()


def serialize_pp(value: NamedTuple) -> str:
    """serialize and pretty print"""
    return serialize_dagster_namedtuple(value, indent=2, separators=(",", ": "))
