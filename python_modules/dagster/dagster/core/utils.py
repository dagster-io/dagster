import random
import string
import uuid

import toposort as toposort_

BACKFILL_TAG_LENGTH = 8


def toposort(data):
    return [sorted(list(level)) for level in toposort_.toposort(data)]


def toposort_flatten(data):
    return [item for level in toposort(data) for item in level]


def make_new_run_id():
    return str(uuid.uuid4())


def make_new_backfill_id():
    return ''.join(random.choice(string.ascii_lowercase) for x in range(BACKFILL_TAG_LENGTH))
