from typing import TYPE_CHECKING, Annotated, Optional

import pytest
from dagster_shared.check import CheckError
from dagster_shared.check.builder import ImportFrom
from dagster_shared.check.decorator import checked

if TYPE_CHECKING:
    from dagster_shared.utils.test import TestType


def test_basic():
    @checked
    def foo(): ...

    foo()

    @checked
    def bar(i: int): ...

    bar(1)
    bar(i=1)
    with pytest.raises(CheckError):
        bar("1")  # type: ignore
    with pytest.raises(CheckError):
        bar(i="1")  # type: ignore


class Thing: ...


def test_many():
    @checked
    def big(
        name: str,
        nick_names: list[str],
        age: int,
        cool: bool,
        thing: Optional[Thing],
        other_thing: Thing,
        percent: float,
        o_s: Optional[str],
        o_n: Optional[int],
        o_f: Optional[float],
        o_b: Optional[bool],
        foos: list[Annotated["TestType", ImportFrom("dagster_shared.utils.test")]],
    ):
        return True

    assert big(
        name="dude",
        nick_names=[
            "foo",
            "bar",
            "biz",
        ],
        age=42,
        cool=False,
        thing=None,
        other_thing=Thing(),
        percent=0.5,
        o_s="x",
        o_n=3,
        o_f=None,
        o_b=None,
        foos=[],
    )

    with pytest.raises(CheckError):
        assert big(
            name="dude",
            nick_names=[
                "foo",
                "bar",
                "biz",
            ],
            age=42,
            cool=False,
            thing=None,
            other_thing=Thing(),
            percent=0.5,
            o_s="x",
            o_n=3,
            o_f="surprise_not_float",  # type: ignore
            o_b=None,
            foos=[],
        )


def test_no_op():
    def foo(): ...

    c_foo = checked(foo)
    assert c_foo is foo

    def bar() -> None: ...

    c_bar = checked(bar)
    assert c_bar is bar


def test_star():
    @checked
    def baz(*, i: int): ...

    baz(i=1)
    with pytest.raises(CheckError):
        baz(i="1")  # type: ignore


def test_partial():
    @checked
    def foo(a, b, c: int): ...

    foo(1, 2, 3)


def test_class():
    class Foo:
        @checked
        def me(self):
            return self

        @checked
        def yell(self, word: str):
            return word

        @staticmethod
        @checked
        def holler(word: str):
            return word

        @classmethod
        @checked
        def scream(cls, word: str):
            return word

    f = Foo()
    f.me()

    f.yell("HI")
    with pytest.raises(CheckError):
        f.yell(3)  # type: ignore

    Foo.holler("hi")
    with pytest.raises(CheckError):
        Foo.holler(3)  # type: ignore

    Foo.scream("hi")
    with pytest.raises(CheckError):
        Foo.scream(3)  # type: ignore


def test_defaults():
    @checked
    def foo(a: int, b: int = 1):
        return a + b

    assert foo(0) == 1

    @checked
    def bar(private_list: list = []):
        private_list.append(1)
        return private_list

    assert bar() == [1]
    assert bar() == [1]  # @checked makes it a not shared container instance

    class GlobalThing:
        def __init__(self):
            self._things = []

        def bump(self):
            self._things.append(1)

        def total(self):
            return sum(self._things)

    _global = GlobalThing()

    @checked
    def baz(shared_inst: GlobalThing = _global):
        _global.bump()
        return _global.total()

    assert baz() == 1
    assert baz() == 2
