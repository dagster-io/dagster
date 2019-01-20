from .decorator import dagster_type, get_runtime_type_on_decorated_klass


@dagster_type
class Sequence(object):
    def __init__(self, iterable):
        self._iterable = iterable

    def items(self):
        for item in self._iterable():
            yield item


SEQUENCE_RUNTIME_TYPE = get_runtime_type_on_decorated_klass(Sequence)
