from typing import NamedTuple, Type

from dagster import _check as check


def serdes_tuple_class(interface_cls: Type) -> Type:
    type_name = interface_cls.__name__
    check.invariant(type_name.startswith("I"), "Expected interface name to start with 'I'")
    entries = []
    for name, type_ in interface_cls.__annotations__.items():
        entries.append((name, type_))
    return NamedTuple(_get_base_class_name(interface_cls), entries)


def _get_base_class_name(interface_cls: Type) -> str:
    return "_" + interface_cls.__name__[1:]
