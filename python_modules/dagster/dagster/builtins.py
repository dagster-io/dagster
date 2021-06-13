import typing

Any = typing.Any
Bool = bool
Float = float
Int = int
Nothing = type(None)
String = str


class BuiltinEnum:

    ANY = Any
    BOOL = Bool
    FLOAT = Float
    INT = Int
    NOTHING = Nothing
    STRING = String

    @classmethod
    def contains(cls, value):
        for ttype in [cls.ANY, cls.BOOL, cls.FLOAT, cls.INT, cls.STRING, cls.NOTHING]:
            if value == ttype:
                return True

        return False
