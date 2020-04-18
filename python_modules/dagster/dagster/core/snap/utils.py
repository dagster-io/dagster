import hashlib

from dagster.serdes import serialize_dagster_namedtuple


def create_snapshot_id(snapshot):
    json_rep = serialize_dagster_namedtuple(snapshot)
    m = hashlib.sha1()  # so that hexdigest is 40, not 64 bytes
    m.update(json_rep.encode())
    return m.hexdigest()
