import pytest
from dagster._check.functions import CheckError
from dagster_components.blueprint import Blueprint, get_blueprint, has_blueprint, scaffold_with


# Example usage:
def test_basic_usage() -> None:
    # Example blueprint class
    class MyBlueprint(Blueprint):
        pass

    # Example decorated class
    @scaffold_with(MyBlueprint)
    class MyClass:
        pass

    # Example undecorated class
    class RegularClass:
        pass

    # Test the functions
    assert has_blueprint(MyClass) is True
    assert has_blueprint(RegularClass) is False
    assert isinstance(get_blueprint(MyClass), MyBlueprint)
    with pytest.raises(CheckError):
        get_blueprint(RegularClass)


def test_inheritance() -> None:
    class ScaffolderOne(Blueprint): ...

    class ScaffolderTwo(Blueprint): ...

    @scaffold_with(ScaffolderOne)
    class ClassOne: ...

    @scaffold_with(ScaffolderTwo)
    class ClassTwo(ClassOne): ...

    assert has_blueprint(ClassOne) is True
    assert isinstance(get_blueprint(ClassOne), ScaffolderOne)

    assert has_blueprint(ClassTwo) is True
    assert isinstance(get_blueprint(ClassTwo), ScaffolderTwo)
