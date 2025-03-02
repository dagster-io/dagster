import pytest
from dagster._check.functions import CheckError
from dagster_components.scaffoldable.decorator import (
    get_scaffolder,
    is_scaffoldable_class,
    scaffoldable,
)
from dagster_components.scaffoldable.scaffolder import Scaffolder


# Example usage:
def test_basic_usage() -> None:
    # Example scaffolder class
    class MyScaffolder(Scaffolder):
        pass

    # Example decorated class
    @scaffoldable(MyScaffolder)
    class MyClass:
        pass

    # Example undecorated class
    class RegularClass:
        pass

    # Test the functions
    assert is_scaffoldable_class(MyClass) is True
    assert is_scaffoldable_class(RegularClass) is False
    assert isinstance(get_scaffolder(MyClass), MyScaffolder)
    with pytest.raises(CheckError):
        get_scaffolder(RegularClass)


def test_inheritance() -> None:
    class ScaffoldableOne(Scaffolder): ...

    class ScaffoldableTwo(Scaffolder): ...

    @scaffoldable(ScaffoldableOne)
    class ClassOne: ...

    @scaffoldable(ScaffoldableTwo)
    class ClassTwo(ClassOne): ...

    assert is_scaffoldable_class(ClassOne) is True
    assert isinstance(get_scaffolder(ClassOne), ScaffoldableOne)

    assert is_scaffoldable_class(ClassTwo) is True
    assert isinstance(get_scaffolder(ClassTwo), ScaffoldableTwo)
