# record depends on check, but check needs to discern records so these pieces are defined here

RECORD_MARKER_VALUE = object()
# "I do want to release this as checkrepublic one day" - schrockn
RECORD_MARKER_FIELD = "__checkrepublic__"


def is_record(obj) -> bool:
    """Whether or not this object was produced by a record decorator."""
    return getattr(obj, RECORD_MARKER_FIELD, None) == RECORD_MARKER_VALUE
