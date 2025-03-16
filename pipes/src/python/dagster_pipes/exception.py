from typing import Optional, List, Any, TypeVar, Callable, Type, cast


T = TypeVar("T")


def from_none(x: Any) -> Any:
    assert x is None
    return x


def from_union(fs, x):
    for f in fs:
        try:
            return f(x)
        except:
            pass
    assert False


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


class CauseContext:
    """exception that being handled when this exception was raised
    
    exception that explicitly led to this exception
    """
    cause: Optional['CauseCause']
    """exception that explicitly led to this exception"""

    context: Optional['CauseContext']
    """exception that being handled when this exception was raised"""

    message: Optional[str]
    name: Optional[str]
    """class name of Exception object"""

    stack: Optional[List[str]]

    def __init__(self, cause: Optional['CauseCause'], context: Optional['CauseContext'], message: Optional[str], name: Optional[str], stack: Optional[List[str]]) -> None:
        self.cause = cause
        self.context = context
        self.message = message
        self.name = name
        self.stack = stack

    @staticmethod
    def from_dict(obj: Any) -> 'CauseContext':
        assert isinstance(obj, dict)
        cause = from_union([CauseCause.from_dict, from_none], obj.get("cause"))
        context = from_union([CauseContext.from_dict, from_none], obj.get("context"))
        message = from_union([from_str, from_none], obj.get("message"))
        name = from_union([from_none, from_str], obj.get("name"))
        stack = from_union([lambda x: from_list(from_str, x), from_none], obj.get("stack"))
        return CauseContext(cause, context, message, name, stack)

    def to_dict(self) -> dict:
        result: dict = {}
        if self.cause is not None:
            result["cause"] = from_union([lambda x: to_class(CauseCause, x), from_none], self.cause)
        if self.context is not None:
            result["context"] = from_union([lambda x: to_class(CauseContext, x), from_none], self.context)
        if self.message is not None:
            result["message"] = from_union([from_str, from_none], self.message)
        if self.name is not None:
            result["name"] = from_union([from_none, from_str], self.name)
        if self.stack is not None:
            result["stack"] = from_union([lambda x: from_list(from_str, x), from_none], self.stack)
        return result


class CauseCause:
    """exception that explicitly led to this exception"""

    cause: Optional['CauseCause']
    """exception that explicitly led to this exception"""

    context: Optional[CauseContext]
    """exception that being handled when this exception was raised"""

    message: Optional[str]
    name: Optional[str]
    """class name of Exception object"""

    stack: Optional[List[str]]

    def __init__(self, cause: Optional['CauseCause'], context: Optional[CauseContext], message: Optional[str], name: Optional[str], stack: Optional[List[str]]) -> None:
        self.cause = cause
        self.context = context
        self.message = message
        self.name = name
        self.stack = stack

    @staticmethod
    def from_dict(obj: Any) -> 'CauseCause':
        assert isinstance(obj, dict)
        cause = from_union([CauseCause.from_dict, from_none], obj.get("cause"))
        context = from_union([CauseContext.from_dict, from_none], obj.get("context"))
        message = from_union([from_str, from_none], obj.get("message"))
        name = from_union([from_none, from_str], obj.get("name"))
        stack = from_union([lambda x: from_list(from_str, x), from_none], obj.get("stack"))
        return CauseCause(cause, context, message, name, stack)

    def to_dict(self) -> dict:
        result: dict = {}
        if self.cause is not None:
            result["cause"] = from_union([lambda x: to_class(CauseCause, x), from_none], self.cause)
        if self.context is not None:
            result["context"] = from_union([lambda x: to_class(CauseContext, x), from_none], self.context)
        if self.message is not None:
            result["message"] = from_union([from_str, from_none], self.message)
        if self.name is not None:
            result["name"] = from_union([from_none, from_str], self.name)
        if self.stack is not None:
            result["stack"] = from_union([lambda x: from_list(from_str, x), from_none], self.stack)
        return result


class ExceptionCause:
    """exception that explicitly led to this exception"""

    cause: Optional[CauseCause]
    """exception that explicitly led to this exception"""

    context: Optional[CauseContext]
    """exception that being handled when this exception was raised"""

    message: Optional[str]
    name: Optional[str]
    """class name of Exception object"""

    stack: Optional[List[str]]

    def __init__(self, cause: Optional[CauseCause], context: Optional[CauseContext], message: Optional[str], name: Optional[str], stack: Optional[List[str]]) -> None:
        self.cause = cause
        self.context = context
        self.message = message
        self.name = name
        self.stack = stack

    @staticmethod
    def from_dict(obj: Any) -> 'ExceptionCause':
        assert isinstance(obj, dict)
        cause = from_union([CauseCause.from_dict, from_none], obj.get("cause"))
        context = from_union([CauseContext.from_dict, from_none], obj.get("context"))
        message = from_union([from_str, from_none], obj.get("message"))
        name = from_union([from_none, from_str], obj.get("name"))
        stack = from_union([lambda x: from_list(from_str, x), from_none], obj.get("stack"))
        return ExceptionCause(cause, context, message, name, stack)

    def to_dict(self) -> dict:
        result: dict = {}
        if self.cause is not None:
            result["cause"] = from_union([lambda x: to_class(CauseCause, x), from_none], self.cause)
        if self.context is not None:
            result["context"] = from_union([lambda x: to_class(CauseContext, x), from_none], self.context)
        if self.message is not None:
            result["message"] = from_union([from_str, from_none], self.message)
        if self.name is not None:
            result["name"] = from_union([from_none, from_str], self.name)
        if self.stack is not None:
            result["stack"] = from_union([lambda x: from_list(from_str, x), from_none], self.stack)
        return result


class ExceptionContext:
    """exception that being handled when this exception was raised
    
    exception that explicitly led to this exception
    """
    cause: Optional[CauseCause]
    """exception that explicitly led to this exception"""

    context: Optional[CauseContext]
    """exception that being handled when this exception was raised"""

    message: Optional[str]
    name: Optional[str]
    """class name of Exception object"""

    stack: Optional[List[str]]

    def __init__(self, cause: Optional[CauseCause], context: Optional[CauseContext], message: Optional[str], name: Optional[str], stack: Optional[List[str]]) -> None:
        self.cause = cause
        self.context = context
        self.message = message
        self.name = name
        self.stack = stack

    @staticmethod
    def from_dict(obj: Any) -> 'ExceptionContext':
        assert isinstance(obj, dict)
        cause = from_union([CauseCause.from_dict, from_none], obj.get("cause"))
        context = from_union([CauseContext.from_dict, from_none], obj.get("context"))
        message = from_union([from_str, from_none], obj.get("message"))
        name = from_union([from_none, from_str], obj.get("name"))
        stack = from_union([lambda x: from_list(from_str, x), from_none], obj.get("stack"))
        return ExceptionContext(cause, context, message, name, stack)

    def to_dict(self) -> dict:
        result: dict = {}
        if self.cause is not None:
            result["cause"] = from_union([lambda x: to_class(CauseCause, x), from_none], self.cause)
        if self.context is not None:
            result["context"] = from_union([lambda x: to_class(CauseContext, x), from_none], self.context)
        if self.message is not None:
            result["message"] = from_union([from_str, from_none], self.message)
        if self.name is not None:
            result["name"] = from_union([from_none, from_str], self.name)
        if self.stack is not None:
            result["stack"] = from_union([lambda x: from_list(from_str, x), from_none], self.stack)
        return result


class Exception:
    cause: Optional[ExceptionCause]
    """exception that explicitly led to this exception"""

    context: Optional[ExceptionContext]
    """exception that being handled when this exception was raised"""

    message: Optional[str]
    name: Optional[str]
    """class name of Exception object"""

    stack: Optional[List[str]]

    def __init__(self, cause: Optional[ExceptionCause], context: Optional[ExceptionContext], message: Optional[str], name: Optional[str], stack: Optional[List[str]]) -> None:
        self.cause = cause
        self.context = context
        self.message = message
        self.name = name
        self.stack = stack

    @staticmethod
    def from_dict(obj: Any) -> 'Exception':
        assert isinstance(obj, dict)
        cause = from_union([ExceptionCause.from_dict, from_none], obj.get("cause"))
        context = from_union([ExceptionContext.from_dict, from_none], obj.get("context"))
        message = from_union([from_str, from_none], obj.get("message"))
        name = from_union([from_none, from_str], obj.get("name"))
        stack = from_union([lambda x: from_list(from_str, x), from_none], obj.get("stack"))
        return Exception(cause, context, message, name, stack)

    def to_dict(self) -> dict:
        result: dict = {}
        if self.cause is not None:
            result["cause"] = from_union([lambda x: to_class(ExceptionCause, x), from_none], self.cause)
        if self.context is not None:
            result["context"] = from_union([lambda x: to_class(ExceptionContext, x), from_none], self.context)
        if self.message is not None:
            result["message"] = from_union([from_str, from_none], self.message)
        if self.name is not None:
            result["name"] = from_union([from_none, from_str], self.name)
        if self.stack is not None:
            result["stack"] = from_union([lambda x: from_list(from_str, x), from_none], self.stack)
        return result


def exception_from_dict(s: Any) -> Exception:
    return Exception.from_dict(s)


def exception_to_dict(x: Exception) -> Any:
    return to_class(Exception, x)
