from functools import cached_property
from typing import NamedTuple


class OtherExample(NamedTuple):
    int_value: int
    str_value: str

    @cached_property
    def added(self) -> str:
        return self.str_value + str(self.int_value)


print(OtherExample(1, "foo").added)
