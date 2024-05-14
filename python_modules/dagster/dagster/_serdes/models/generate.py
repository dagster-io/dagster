from typing import Iterable, Tuple, Type

from serdes_spec import SerdesModelSpec

from dagster import _check as check
from dagster._seven import import_module_from_path, is_subclass
from dagster._utils import file_relative_path
from dagster._utils.indenting_printer import IndentingPrinter


class SerdesModelGen:
    def __init__(self, spec_type) -> None:
        self.spec_type = spec_type

    @property
    def name(self) -> str:
        return self.spec_type.__name__

    def fields(self) -> Iterable[Tuple[str, Type]]:
        for field_name, field_type in self.spec_type.__annotations__.items():
            yield field_name, field_type


TYPE_STR_MAP = {
    int: "int",
    str: "str",
}


def str_for_type(t: Type) -> str:
    return TYPE_STR_MAP[t]


def check_line_for_type(t: Type, name: str) -> str:
    if t in {int, str}:
        return f"check.{t.__name__}_param({name}, {name})"

    check.invariant(f"Unsupported type {t}")


def generate_serdes_model(model_gen: SerdesModelGen) -> None:
    preamble = """
from typing import NamedTuple

from dagster import _check as check


"""

    printer = IndentingPrinter(indent_level=4)
    printer.append(preamble)

    printer.line(f"class {model_gen.name}(")
    with printer.with_indent():
        printer.line(f'NamedTuple("{model_gen.spec_type.__name__}", [')
        with printer.with_indent():
            for field_name, field_type in model_gen.fields():
                printer.line(f'("{field_name}", {str_for_type(field_type)}),')
        printer.line("],")
    printer.line("):")

    with printer.with_indent():
        for field_name, field_type in model_gen.fields():
            printer.line(f"{field_name}: {str_for_type(field_type)}")

        printer.line("")
        printer.line("def __new__(")
        with printer.with_indent():
            printer.line("cls,")
            printer.line("*")
            for field_name, field_type in model_gen.fields():
                printer.line(f"{field_name}: {str_for_type(field_type)},")
        printer.line(f') -> "{model_gen.name}":')
        with printer.with_indent():
            printer.line("return super().__new__(")
            with printer.with_indent():
                printer.line("cls,")
                for field_name, field_type in model_gen.fields():
                    printer.line(
                        f'check.{field_type.__name__}_param({field_name}, "{field_name}"),'
                    )
            printer.line(")")


if __name__ == "__main__":
    mod = import_module_from_path("specs", file_relative_path(__file__, "specs.py"))

    specs = []
    for symbol in mod.__dict__.values():
        if symbol is SerdesModelSpec:
            continue
        if is_subclass(symbol, SerdesModelSpec):
            specs.append(symbol)

    single_model_gen = SerdesModelGen(next(iter(specs)))

    generate_serdes_model(single_model_gen)
