from checked_named_tuple_spec import CheckedNamedTupleSpec


class ExampleDataClass(CheckedNamedTupleSpec):
    int_value: int
    str_value: str


class Base(CheckedNamedTupleSpec):
    int_value: int


class Derived(Base):
    str_value: str
