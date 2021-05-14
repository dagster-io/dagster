from dagster import solid, usable_as_dagster_type


@usable_as_dagster_type
class EvenType:
    def __init__(self, num):
        assert num % 2 is 0
        self.num = num


@solid
def double_even(even_num: EvenType) -> EvenType:
    return EvenType(even_num.num * 2)
