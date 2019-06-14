import sys

if sys.version_info.major >= 3:
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


else:
    from enum import Enum

    class BuiltinEnum(Enum):

        ANY = 'Any'
        BOOL = 'Bool'
        FLOAT = 'Float'
        INT = 'Int'
        PATH = 'Path'
        STRING = 'String'
        NOTHING = 'Nothing'

        @classmethod
        def contains(cls, value):
            return isinstance(value, cls)
