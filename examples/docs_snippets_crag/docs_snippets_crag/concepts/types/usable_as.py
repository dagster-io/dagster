from dagster import op, usable_as_dagster_type


@usable_as_dagster_type
class EvenType:
    def __init__(self, num):
        assert num % 2 is 0
        self.num = num


@op
def double_even(even_num: EvenType) -> EvenType:
    return EvenType(even_num.num * 2)
