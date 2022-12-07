# isort: off


def read_some_file():
    return "foo"


# start_marker
from hashlib import sha256
from dagster import LogicalVersion, observable_source_asset


@observable_source_asset
def foo_source_asset(_context):
    content = read_some_file()
    hash_sig = sha256()
    hash_sig.update(bytearray(content, "utf8"))
    return LogicalVersion(hash_sig.hexdigest())


# end_marker
