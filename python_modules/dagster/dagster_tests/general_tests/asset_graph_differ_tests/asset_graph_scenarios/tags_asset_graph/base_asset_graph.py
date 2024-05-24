from dagster import Definitions, asset


@asset(tags={"foo": "bar", "one": "two"})
def upstream():
    return 1


@asset(tags={"baz": "qux"})
def downstream(upstream):
    return upstream + 1


@asset(tags={"red": "apple", "yellow": "banana"})
def fruits():
    return 1


@asset(tags={"a": "A", "b": "B"})
def letters():
    return 1


@asset(tags={"one": "1", "two": "2", "three": "3"})
def numbers():
    return 1


defs = Definitions(assets=[upstream, downstream, numbers, letters, fruits])
