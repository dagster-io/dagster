import typing


class BuiltinEnum:

    ANY = typing.Any
    # mypy doesn't like the mismatch between BOOL and "Bool"
    BOOL = typing.NewType("Bool", bool)  # type: ignore[misc]
    FLOAT = typing.NewType("Float", float)  # type: ignore[misc]
    INT = typing.NewType("Int", int)  # type: ignore[misc]
    STRING = typing.NewType("String", str)  # type: ignore[misc]
    NOTHING = typing.NewType("Nothing", None)  # type: ignore[misc]

    @classmethod
    def contains(cls, value):
        for ttype in [cls.ANY, cls.BOOL, cls.FLOAT, cls.INT, cls.STRING, cls.NOTHING]:
            if value == ttype:
                return True

        return False


Any = BuiltinEnum.ANY
String = BuiltinEnum.STRING
Int = BuiltinEnum.INT
Bool = BuiltinEnum.BOOL
Float = BuiltinEnum.FLOAT
Nothing = BuiltinEnum.NOTHING
