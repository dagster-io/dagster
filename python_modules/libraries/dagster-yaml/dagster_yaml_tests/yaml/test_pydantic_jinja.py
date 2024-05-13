from dagster_yaml.yaml.pydantic_jinja import (
    JinjaStr,
    JinjaStrNone,
    OptionalJinjaStr,
)
from dagster_yaml.yaml.pydantic_yaml import parse_yaml_file
from pydantic import BaseModel


def test_pydantic_jinja_smoke() -> None:
    class MyModel(BaseModel):
        required: JinjaStr
        optional1: OptionalJinjaStr = JinjaStrNone
        optional2: OptionalJinjaStr = JinjaStrNone

    parsed = parse_yaml_file(
        MyModel, "{'required': 'foo {{ var1 }}',\n'optional1': 'bar {{ var2 }}'}"
    )

    assert parsed.required.template == "foo {{ var1 }}"
    assert parsed.required.render() == "foo "
    assert parsed.required.render({"var1": "bar"}) == "foo bar"
    assert str(parsed.required._object_mapping_context.source_position) == "<string>:1"  # type: ignore # noqa: SLF001
    assert str(parsed.optional1._object_mapping_context.source_position) == "<string>:2"  # type: ignore # noqa: SLF001
