import uuid

import toposort as toposort_


def toposort(data):
    return [sorted(list(level)) for level in toposort_.toposort(data)]


def toposort_flatten(data):
    return [item for level in toposort(data) for item in level]


def make_new_run_id():
    return str(uuid.uuid4())
