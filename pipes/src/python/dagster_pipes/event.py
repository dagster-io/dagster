from enum import Enum
from typing import Dict, Any, Optional, TypeVar, Callable, Type, cast


T = TypeVar("T")
EnumT = TypeVar("EnumT", bound=Enum)


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def from_none(x: Any) -> Any:
    assert x is None
    return x


def from_dict(f: Callable[[Any], T], x: Any) -> Dict[str, T]:
    assert isinstance(x, dict)
    return { k: f(v) for (k, v) in x.items() }


def from_union(fs, x):
    for f in fs:
        try:
            return f(x)
        except:
            pass
    assert False


def to_enum(c: Type[EnumT], x: Any) -> EnumT:
    assert isinstance(x, c)
    return x.value


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


class Method(Enum):
    """Event type"""

    CLOSED = "closed"
    LOG = "log"
    OPENED = "opened"
    REPORT_ASSET_CHECK = "report_asset_check"
    REPORT_ASSET_MATERIALIZATION = "report_asset_materialization"
    REPORT_CUSTOM_MESSAGE = "report_custom_message"


class Event:
    dagster_pipes_version: str
    """The version of the Dagster Pipes protocol"""

    method: Method
    """Event type"""

    params: Optional[Dict[str, Dict[str, Any]]]
    """Event parameters"""

    def __init__(self, dagster_pipes_version: str, method: Method, params: Optional[Dict[str, Dict[str, Any]]]) -> None:
        self.dagster_pipes_version = dagster_pipes_version
        self.method = method
        self.params = params

    @staticmethod
    def from_dict(obj: Any) -> 'Event':
        assert isinstance(obj, dict)
        dagster_pipes_version = from_str(obj.get("__dagster_pipes_version"))
        method = Method(obj.get("method"))
        params = from_union([from_none, lambda x: from_dict(lambda x: from_dict(lambda x: x, x), x)], obj.get("params"))
        return Event(dagster_pipes_version, method, params)

    def to_dict(self) -> dict:
        result: dict = {}
        result["__dagster_pipes_version"] = from_str(self.dagster_pipes_version)
        result["method"] = to_enum(Method, self.method)
        result["params"] = from_union([from_none, lambda x: from_dict(lambda x: from_dict(lambda x: x, x), x)], self.params)
        return result


def event_from_dict(s: Any) -> Event:
    return Event.from_dict(s)


def event_to_dict(x: Event) -> Any:
    return to_class(Event, x)
