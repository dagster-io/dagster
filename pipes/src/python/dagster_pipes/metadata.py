from enum import Enum
from typing import Dict, Any, List, Union, Optional, TypeVar, Callable, Type, cast


T = TypeVar("T")
EnumT = TypeVar("EnumT", bound=Enum)


def from_int(x: Any) -> int:
    assert isinstance(x, int) and not isinstance(x, bool)
    return x


def from_float(x: Any) -> float:
    assert isinstance(x, (float, int)) and not isinstance(x, bool)
    return float(x)


def from_dict(f: Callable[[Any], T], x: Any) -> Dict[str, T]:
    assert isinstance(x, dict)
    return { k: f(v) for (k, v) in x.items() }


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


def from_bool(x: Any) -> bool:
    assert isinstance(x, bool)
    return x


def from_none(x: Any) -> Any:
    assert x is None
    return x


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def from_union(fs, x):
    for f in fs:
        try:
            return f(x)
        except:
            pass
    assert False


def to_float(x: Any) -> float:
    assert isinstance(x, float)
    return x


def to_enum(c: Type[EnumT], x: Any) -> EnumT:
    assert isinstance(x, c)
    return x.value


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


class TypeEnum(Enum):
    ASSET = "asset"
    BOOL = "bool"
    DAGSTER_RUN = "dagster_run"
    FLOAT = "float"
    INFER = "__infer__"
    INT = "int"
    JSON = "json"
    MD = "md"
    NOTEBOOK = "notebook"
    NULL = "null"
    PATH = "path"
    TEXT = "text"
    URL = "url"


class Metadata:
    raw_value: Optional[Union[int, float, Dict[str, Any], List[Any], bool, str]]
    type: Optional[TypeEnum]

    def __init__(self, raw_value: Optional[Union[int, float, Dict[str, Any], List[Any], bool, str]], type: Optional[TypeEnum]) -> None:
        self.raw_value = raw_value
        self.type = type

    @staticmethod
    def from_dict(obj: Any) -> 'Metadata':
        assert isinstance(obj, dict)
        raw_value = from_union([from_int, from_float, lambda x: from_dict(lambda x: x, x), lambda x: from_list(lambda x: x, x), from_bool, from_none, from_str], obj.get("raw_value"))
        type = from_union([TypeEnum, from_none], obj.get("type"))
        return Metadata(raw_value, type)

    def to_dict(self) -> dict:
        result: dict = {}
        if self.raw_value is not None:
            result["raw_value"] = from_union([from_int, to_float, lambda x: from_dict(lambda x: x, x), lambda x: from_list(lambda x: x, x), from_bool, from_none, from_str], self.raw_value)
        if self.type is not None:
            result["type"] = from_union([lambda x: to_enum(TypeEnum, x), from_none], self.type)
        return result


def metadata_from_dict(s: Any) -> Metadata:
    return Metadata.from_dict(s)


def metadata_to_dict(x: Metadata) -> Any:
    return to_class(Metadata, x)
