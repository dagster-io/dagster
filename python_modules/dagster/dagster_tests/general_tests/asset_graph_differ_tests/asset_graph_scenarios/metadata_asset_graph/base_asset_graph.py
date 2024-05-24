from dagster import Definitions, asset


@asset(metadata={"foo": "bar", "one": "two"})
def upstream():
    return 1


@asset(metadata={"baz": "qux"})
def downstream(upstream):
    return upstream + 1


@asset(metadata={"red": "apple", "yellow": "banana"})
def fruits():
    return 1


@asset(metadata={"a": "A", "b": "B"})
def letters():
    return 1


@asset(metadata={"one": "1", "two": "2", "three": "3"})
def numbers():
    return 1


defs = Definitions(assets=[upstream, downstream, numbers, letters, fruits])
