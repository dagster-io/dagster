from dagster import _seven

PICKLE_PROTOCOL = 2


def is_json_serializable(value):
    try:
        _seven.json.dumps(value)
        return True
    except TypeError:
        return False
