import pytest
from dagster._check.functions import CheckError
from dagster_components.scaffoldable.decorator import (
    get_scaffolder,
    is_scaffoldable_class,
    scaffoldable,
)
from dagster_components.scaffoldable.scaffolder import ComponentScaffolder


# Example usage:
def test_basic_usage() -> None:
    # Example scaffolder class
    class MyScaffolder(ComponentScaffolder):
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
    assert get_scaffolder(MyClass) is MyScaffolder
    with pytest.raises(CheckError):
        get_scaffolder(RegularClass)


def test_inheritance() -> None:
    class ScaffoldableOne(ComponentScaffolder): ...

    class ScaffoldableTwo(ComponentScaffolder): ...

    @scaffoldable(ScaffoldableOne)
    class ClassOne: ...

    @scaffoldable(ScaffoldableTwo)
    class ClassTwo(ClassOne): ...

    assert is_scaffoldable_class(ClassOne) is True
    assert get_scaffolder(ClassOne) is ScaffoldableOne

    assert is_scaffoldable_class(ClassTwo) is True
    assert get_scaffolder(ClassTwo) is ScaffoldableTwo
