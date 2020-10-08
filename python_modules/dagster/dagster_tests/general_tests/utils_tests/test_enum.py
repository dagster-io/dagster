from enum import Enum

from dagster.utils import is_enum_value


class APythonEnum(Enum):
    VAL = "VAL"


def test_enum_value():
    assert is_enum_value(None) is False
    assert is_enum_value(1) is False
    assert is_enum_value("foo") is False
    assert is_enum_value("VAL") is False
    assert is_enum_value(APythonEnum.VAL) is True
