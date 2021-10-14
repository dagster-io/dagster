from dagster import PythonObjectDagsterType, make_python_type_usable_as_dagster_type, op


class EvenType:
    def __init__(self, num):
        assert num % 2 is 0
        self.num = num


EvenDagsterType = PythonObjectDagsterType(EvenType, name="EvenDagsterType")

make_python_type_usable_as_dagster_type(EvenType, EvenDagsterType)


@op
def double_even(even_num: EvenType) -> EvenType:
    return EvenType(even_num.num * 2)
