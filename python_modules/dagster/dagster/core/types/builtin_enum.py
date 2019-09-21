import typing


class BuiltinEnum:

    ANY = typing.Any
    BOOL = typing.NewType('Bool', bool)
    FLOAT = typing.NewType('Float', float)
    INT = typing.NewType('Int', int)
    PATH = typing.NewType('Path', str)
    STRING = typing.NewType('String', str)
    NOTHING = typing.NewType('Nothing', None)

    @classmethod
    def contains(cls, value):
        return any(value == getattr(cls, key) for key in dir(cls))
