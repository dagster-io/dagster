from dagster._core.utils import strict_dataclass


def test_frozen():
    pass


def test_positional_arguments():
    pass


def test_too_many_positional_arguments():
    @strict_dataclass()
    def MyClass():
        a: int

    MyClass(5, 6)
