import pytest
from dagster._check.functions import CheckError
from dagster_components.scaffolder import Scaffolder, get_scaffolder, has_scaffolder, scaffolder


# Example usage:
def test_basic_usage() -> None:
    # Example scaffolder class
    class MyScaffolder(Scaffolder):
        pass

    # Example decorated class
    @scaffolder(MyScaffolder)
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

    @scaffolder(ScaffolderOne)
    class ClassOne: ...

    @scaffolder(ScaffolderTwo)
    class ClassTwo(ClassOne): ...

    assert has_scaffolder(ClassOne) is True
    assert isinstance(get_scaffolder(ClassOne), ScaffolderOne)

    assert has_scaffolder(ClassTwo) is True
    assert isinstance(get_scaffolder(ClassTwo), ScaffolderTwo)
