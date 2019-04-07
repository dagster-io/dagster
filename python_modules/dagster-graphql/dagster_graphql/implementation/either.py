class Either(object):
    def __init__(self, value):
        self._value = value

    def value(self):
        return self._value

    def value_or_raise(self):
        if isinstance(self, EitherValue):
            return self.value()
        else:
            error = self.value()
            if hasattr(error, 'message'):
                raise Exception(error.message)
            else:
                raise Exception(str(error))

    def chain(self, fn):
        raise NotImplementedError('Subclasses of Either must override chain.')


class EitherValue(Either):
    def chain(self, fn):
        result = fn(self.value())
        if isinstance(result, Either):
            return result
        else:
            return EitherValue(result)


class EitherError(Either):
    def chain(self, fn):
        return self
