import pytest
from dagster_components.scaffold.scaffold import (
    Scaffolder,
    get_scaffolder,
    has_scaffolder,
    scaffold_with,
)
from dagster_shared.check import CheckError


# Example usage:
def test_basic_usage() -> None:
    # Example scaffolder class
    class MyScaffolder(Scaffolder):
        pass

    # Example decorated class
    @scaffold_with(MyScaffolder)
    class MyClass:
        pass

    # Example undecorated class
    class RegularClass:
        pass

    # Test the functions
    assert has_scaffolder(MyClass) is True
    assert has_scaffolder(RegularClass) is False
    assert isinstance(get_scaffolder(MyClass), MyScaffolder)
    with pytest.raises(CheckError):
        get_scaffolder(RegularClass)


def test_inheritance() -> None:
    class ScaffolderOne(Scaffolder): ...

    class ScaffolderTwo(Scaffolder): ...

    @scaffold_with(ScaffolderOne)
    class ClassOne: ...

    @scaffold_with(ScaffolderTwo)
    class ClassTwo(ClassOne): ...

    assert has_scaffolder(ClassOne) is True
    assert isinstance(get_scaffolder(ClassOne), ScaffolderOne)

    assert has_scaffolder(ClassTwo) is True
    assert isinstance(get_scaffolder(ClassTwo), ScaffolderTwo)
