import typing

from dagster import PythonObjectDagsterType, solid


class EvenType:
    def __init__(self, num):
        assert num % 2 is 0
        self.num = num


if typing.TYPE_CHECKING:
    EvenDagsterType = EvenType
else:
    EvenDagsterType = PythonObjectDagsterType(EvenType)


@solid
def double_even(_, even_num: EvenDagsterType) -> EvenDagsterType:
    return EvenType(even_num.num * 2)
