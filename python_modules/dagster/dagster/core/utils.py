import random
import string
import uuid
import warnings

import toposort as toposort_
from dagster.version import __version__

BACKFILL_TAG_LENGTH = 8


def toposort(data):
    return [sorted(list(level)) for level in toposort_.toposort(data)]


def toposort_flatten(data):
    return [item for level in toposort(data) for item in level]


def make_new_run_id():
    return str(uuid.uuid4())


def make_new_backfill_id():
    return "".join(random.choice(string.ascii_lowercase) for x in range(BACKFILL_TAG_LENGTH))


def str_format_list(items):
    return "[{items}]".format(items=", ".join(["'{item}'".format(item=item) for item in items]))


def str_format_set(items):
    return "[{items}]".format(items=", ".join(["'{item}'".format(item=item) for item in items]))


def check_dagster_package_version(library_name, library_version):
    if __version__ != library_version:
        message = "Found version mismatch between `dagster` ({}) and `{}` ({})".format(
            __version__, library_name, library_version
        )
        warnings.warn(message)
