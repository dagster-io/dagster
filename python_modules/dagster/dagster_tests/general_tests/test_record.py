import pickle
from abc import ABC, abstractmethod
from functools import cached_property
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

import pytest
from dagster._record import (
    _INJECTED_DEFAULT_VALS_LOCAL_VAR,
    IHaveNew,
    ImportFrom,
    build_args_and_assignment_strs,
    check,
    copy,
    record,
    record_custom,
)
from dagster._utils.cached_method import cached_method
from typing_extensions import Annotated

if TYPE_CHECKING:
    from dagster._core.test_utils import TestType


def test_kwargs_only() -> None:
    @record
    class MyClass:
        foo: str

    with pytest.raises(TypeError, match="takes 1 positional argument but 2 were given"):
        MyClass("fdslk")  # type: ignore # good job type checker


def test_runtime_typecheck() -> None:
    @record
    class MyClass:
        foo: str
        bar: int

    with pytest.raises(check.CheckError):
        MyClass(foo="fdsjk", bar="fdslk")  # type: ignore # good job type checker


def test_override_constructor_in_subclass() -> None:
    @record
    class MyClass:
        foo: str
        bar: int

        def __new__(cls, foo: str, bar: int):
            return super().__new__(
                cls,
                foo=foo,  # type: ignore
                bar=bar,  # type: ignore
            )

    assert MyClass(foo="fdsjk", bar=4)


def test_override_constructor_in_subclass_different_arg_names() -> None:
    @record_custom
    class MyClass(IHaveNew):
        foo: str
        bar: int

        def __new__(cls, fooarg: str, bararg: int):
            return super().__new__(
                cls,
                foo=fooarg,
                bar=bararg,
            )

    assert MyClass(fooarg="fdsjk", bararg=4)


def test_override_constructor_in_subclass_wrong_type() -> None:
    @record_custom
    class MyClass(IHaveNew):
        foo: str
        bar: int

        def __new__(cls, foo: str, bar: str):
            return super().__new__(
                cls,
                foo=foo,
                bar=bar,
            )

    with pytest.raises(check.CheckError):
        MyClass(foo="fdsjk", bar="fdslk")


def test_model_copy() -> None:
    @record
    class MyClass2:
        foo: str
        bar: int

    obj = MyClass2(foo="abc", bar=5)

    assert copy(obj, foo="xyz") == MyClass2(foo="xyz", bar=5)
    assert copy(obj, bar=6) == MyClass2(foo="abc", bar=6)
    assert copy(obj, foo="xyz", bar=6) == MyClass2(foo="xyz", bar=6)


def test_non_record_param():
    class SomeClass: ...

    class OtherClass: ...

    @record
    class MyModel2:
        some_class: SomeClass

    assert MyModel2(some_class=SomeClass())

    with pytest.raises(check.CheckError):
        MyModel2(some_class=OtherClass())  # wrong class

    with pytest.raises(check.CheckError):
        MyModel2(some_class=SomeClass)  # forgot ()


def test_cached_method() -> None:
    @record()
    class CoolModel2:
        name: str

        @cached_method
        def calculate(self, n: int):
            return {self.name: n}

        @cached_method
        def reticulate(self, n: int):
            return {self.name: n}

        @property
        @cached_method
        def prop(self):
            return {"four": 4}

    m = CoolModel2(name="bob")
    assert m.calculate(4) is m.calculate(4)
    assert m.calculate(4) is not m.reticulate(4)
    assert m.prop is m.prop

    clean_m = CoolModel2(name="bob")
    # cache doesn't effect equality
    assert clean_m == m
    assert m == clean_m

    # cache doesn't effect hash
    s = {m, clean_m}
    assert len(s) == 1

    # cache erased on copy
    m_copy = copy(m)
    assert m_copy.calculate(4) is not m.calculate(4)


def test_forward_ref() -> None:
    @record
    class Parent:
        partner: Optional["Parent"]
        child: Optional["Child"]

    class Child: ...

    assert Parent(partner=None, child=None)


def test_forward_ref_with_new() -> None:
    @record_custom
    class Parent:
        partner: Optional["Parent"]
        child: Optional["Child"]

        def __new__(cls, partner=None, child=None):
            return super().__new__(
                cls,
                partner=partner,
                child=child,
            )

    class Child: ...

    assert Parent()


def _empty_callsite_scope(cls, arg):
    cls(local=arg)


def test_frame_capture() -> None:
    class LocalAtDefineTime: ...

    val = LocalAtDefineTime()

    @record
    class Direct:
        local: Optional["LocalAtDefineTime"]

    _empty_callsite_scope(Direct, val)

    @record()  # invoking decorator has different frame depth from direct
    class InDirect:
        local: Optional["LocalAtDefineTime"]

    _empty_callsite_scope(InDirect, val)

    @record_custom
    class DirectNew:
        local: Optional["LocalAtDefineTime"]

        def __new__(cls, **kwargs):
            super().__new__(cls, **kwargs)

    _empty_callsite_scope(DirectNew, val)

    @record_custom()
    class InDirectNew:
        local: Optional["LocalAtDefineTime"]

        def __new__(cls, **kwargs):
            super().__new__(cls, **kwargs)

    _empty_callsite_scope(InDirectNew, val)


def test_didnt_override_new():
    with pytest.raises(check.CheckError):

        @record_custom()
        class Failed:
            local: Optional[str]

    with pytest.raises(check.CheckError):

        @record_custom
        class FailedAgain:
            local: Optional[str]


def test_empty():
    @record
    class Empty: ...

    assert Empty()


def test_optional_arg() -> None:
    @record
    class Opt:
        maybe: Optional[str] = None
        always: Optional[str]

    assert Opt(always="set")
    assert Opt(always="set", maybe="x").maybe == "x"

    @record(checked=False)
    class Other:
        maybe: Optional[str] = None
        always: Optional[str]

    assert Other(always="set")
    assert Other(always="set", maybe="x").maybe == "x"


def test_dont_share_containers() -> None:
    @record
    class Empties:
        items: List[str] = []
        map: Dict[str, str] = {}

    e_1 = Empties()
    e_2 = Empties()
    assert e_1.items is not e_2.items
    assert e_1.map is not e_2.map


def test_sentinel():
    _unset = object()

    @record
    class Sample:
        val: Optional[Any] = _unset

    assert Sample().val is _unset
    assert Sample(val=None).val is None

    @record(checked=False)
    class OtherSample:
        val: Optional[Any] = _unset

    assert OtherSample().val is _unset
    assert OtherSample(val=None).val is None


@pytest.mark.parametrize(
    "fields, defaults, expected",
    [
        (
            {"name": str},
            {},
            (
                ", *, name",
                "",
            ),
        ),
        # defaults dont need to be in certain order since we force kwargs
        # None handled directly by arg default
        (
            {"name": str, "age": int, "f": float},
            {"age": None},
            (
                ", *, name, age = None, f",
                "",
            ),
        ),
        # empty container defaults get fresh copies via assignments
        (
            {"things": list},
            {"things": []},
            (
                ", *, things = None",
                "things = things if things is not None else []",
            ),
        ),
        (
            {"map": dict},
            {"map": {}},
            (
                ", *, map = None",
                "map = map if map is not None else {}",
            ),
        ),
        # base case - default values resolved by reference to injected local
        (
            {"val": Any},
            {"val": object()},
            (
                f", *, val = {_INJECTED_DEFAULT_VALS_LOCAL_VAR}['val']",
                "",
            ),
        ),
    ],
)
def test_build_args_and_assign(fields, defaults, expected):
    # tests / documents shared utility fn
    # don't hesitate to delete this upon refactor
    assert build_args_and_assignment_strs(fields, defaults) == expected


@record
class Person:
    name: str
    age: int


@record_custom
class Agent(IHaveNew):
    name: str
    secrets: List[str]

    def __new__(cls, name: str, **kwargs):
        return super().__new__(
            cls,
            name=name,
            secrets=kwargs.get("secrets", []),
        )


def test_pickle():
    p = Person(name="Lyra", age=2)
    assert p == pickle.loads(pickle.dumps(p))

    a = Agent(name="smith", secrets=["many"])
    assert a == pickle.loads(pickle.dumps(a))

    a2 = Agent(name="mr. clean")
    assert a2 == pickle.loads(pickle.dumps(a2))


def test_base_class_conflicts() -> None:
    class ConflictPropBase(ABC):
        @property
        def prop(self): ...

    with pytest.raises(check.CheckError, match="Conflicting non-abstract @property"):

        @record
        class X(ConflictPropBase):
            prop: Any

    class AbsPropBase(ABC):
        @property
        @abstractmethod
        def abstract_prop(self): ...

        @property
        @abstractmethod
        def abstract_prop_with_default(self) -> int: ...

    class DidntImpl(AbsPropBase): ...

    with pytest.raises(
        TypeError,
        match="Can't instantiate abstract class DidntImpl",
    ):
        DidntImpl()  # type: ignore # good job type checker

    @record
    class A(AbsPropBase):
        abstract_prop: Any
        abstract_prop_with_default: int = 0

    assert A(abstract_prop=4).abstract_prop == 4
    assert A(abstract_prop=4).abstract_prop_with_default == 0

    class ConflictFnBase:
        def some_method(self): ...

    with pytest.raises(check.CheckError, match="Conflicting function"):

        @record
        class _(ConflictFnBase):
            some_method: Any

    with pytest.raises(check.CheckError, match="will have to override __new__"):

        def _some_func():
            return 4

        @record
        class _:
            thing: Any = _some_func


def test_lazy_import():
    @record
    class BadModel:
        foos: List["TestType"]

    with pytest.raises(check.CheckError, match="Unable to resolve"):
        BadModel(foos=[])

    @record
    class AnnotatedModel:
        foos: List[Annotated["TestType", ImportFrom("dagster._core.test_utils")]]

    assert AnnotatedModel(foos=[])

    with pytest.raises(
        check.CheckError, match="Expected <class 'dagster._core.test_utils.TestType'>"
    ):
        AnnotatedModel(foos=[1, 2, 3])

    def _out_of_scope():
        from dagster._core.test_utils import TestType

        return AnnotatedModel(foos=[TestType()])

    assert _out_of_scope()


class Complex:
    def __init__(self, s: str):
        self.s = s


@record_custom(field_to_new_mapping={"foo_str": "foo"})
class Remapped(IHaveNew):
    foo_str: str

    def __new__(cls, foo: Union[str, Complex]):
        if isinstance(foo, Complex):
            foo = foo.s

        return super().__new__(
            cls,
            foo_str=foo,
        )

    @cached_property
    def foo(self) -> Complex:
        return Complex(self.foo_str)


def test_new_remaps_fields() -> None:
    r = Remapped(foo="test")
    assert r.foo.s == "test"
    r2 = copy(r)
    assert r2.foo.s == "test"

    assert pickle.loads(pickle.dumps(r)) == r


def test_docs():
    @record
    class Documented:
        """So much to know about this class."""

    assert Documented.__doc__
