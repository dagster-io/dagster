from dagster import seven

PICKLE_PROTOCOL = 2


def is_json_serializable(value):
    try:
        seven.json.dumps(value)
        return True
    except TypeError:
        return False
