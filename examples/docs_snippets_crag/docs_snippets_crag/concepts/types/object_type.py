from dagster import PythonObjectDagsterType, op


# start_object_type
class EvenType:
    def __init__(self, num):
        assert num % 2 is 0
        self.num = num


EvenDagsterType = PythonObjectDagsterType(EvenType, name="EvenDagsterType")
# end_object_type

# start_use_object_type
@op
def double_even(even_num: EvenDagsterType) -> EvenDagsterType:
    return EvenType(even_num.num * 2)


# end_use_object_type
