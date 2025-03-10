import pytest
from dagster._check.functions import CheckError
from dagster_components.fold.decorator import foldable, get_scaffolder, is_foldable
from dagster_components.fold.scaffolder import Scaffolder


# Example usage:
def test_basic_usage() -> None:
    # Example scaffolder class
    class MyScaffolder(Scaffolder):
        pass

    # Example decorated class
    @foldable(MyScaffolder)
    class MyClass:
        pass

    # Example undecorated class
    class RegularClass:
        pass

    # Test the functions
    assert is_foldable(MyClass) is True
    assert is_foldable(RegularClass) is False
    assert isinstance(get_scaffolder(MyClass), MyScaffolder)
    with pytest.raises(CheckError):
        get_scaffolder(RegularClass)


def test_inheritance() -> None:
    class ScaffoldableOne(Scaffolder): ...

    class ScaffoldableTwo(Scaffolder): ...

    @foldable(ScaffoldableOne)
    class ClassOne: ...

    @foldable(ScaffoldableTwo)
    class ClassTwo(ClassOne): ...

    assert is_foldable(ClassOne) is True
    assert isinstance(get_scaffolder(ClassOne), ScaffoldableOne)

    assert is_foldable(ClassTwo) is True
    assert isinstance(get_scaffolder(ClassTwo), ScaffoldableTwo)
