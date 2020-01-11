import typing


class BuiltinEnum(object):

    ANY = typing.Any
    BOOL = typing.NewType('Bool', bool)
    FLOAT = typing.NewType('Float', float)
    INT = typing.NewType('Int', int)
    PATH = typing.NewType('Path', str)
    STRING = typing.NewType('String', str)
    NOTHING = typing.NewType('Nothing', None)

    @classmethod
    def contains(cls, value):
        for ttype in [cls.ANY, cls.BOOL, cls.FLOAT, cls.INT, cls.PATH, cls.STRING, cls.NOTHING]:
            if value == ttype:
                return True

        return False


Any = BuiltinEnum.ANY
String = BuiltinEnum.STRING
Int = BuiltinEnum.INT
Bool = BuiltinEnum.BOOL
Path = BuiltinEnum.PATH
Float = BuiltinEnum.FLOAT
Nothing = BuiltinEnum.NOTHING
