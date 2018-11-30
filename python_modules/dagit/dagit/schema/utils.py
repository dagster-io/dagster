import graphene


def non_null_list(ttype):
    return graphene.NonNull(graphene.List(graphene.NonNull(ttype)))


class SomethingOrError(object):
    def __init__(self, it, is_error=None):
        self._it = it
        self._is_error = is_error

    def chain(self, fn):
        if self._is_error and self._is_error(self._it):
            return self
        else:
            result = fn(self._it)
            if isinstance(result, SomethingOrError):
                return result
            else:
                return SomethingOrError(result)

    def get(self):
        return self._it
