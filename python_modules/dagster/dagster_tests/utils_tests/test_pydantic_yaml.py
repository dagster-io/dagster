import traceback

import pytest
from dagster._utils.pydantic_yaml import parse_yaml_file_to_pydantic
from dagster._utils.source_position import HasSourcePositionAndKeyPath
from pydantic import BaseModel, ValidationError


def test_parse_yaml_file_to_pydantic_error() -> None:
    class BrokenModel2(BaseModel):
        bar: str

    class BrokenModel(BaseModel):
        foo: list[BrokenModel2]

    with pytest.raises(ValidationError) as excinfo:
        parse_yaml_file_to_pydantic(BrokenModel, "foo:\n  - bar: 1")

    e = excinfo.value
    e_str = "".join(traceback.format_exception(type(e), e, e.__traceback__))

    assert "foo.0.bar at <string>:2" in e_str
    # No funny business with showing the same exception twice, which can happen with
    # "During handling of the above exception, another exception occurred"
    assert e_str.count("ValidationError:") == 1


def test_parse_yaml_file_to_pydantic() -> None:
    class MyModel2(BaseModel, HasSourcePositionAndKeyPath):
        name: str

    class MyModel(BaseModel):
        child: MyModel2

    rv = parse_yaml_file_to_pydantic(MyModel, "child:\n  name: foo")
    assert rv.child.name == "foo"
    assert str(rv.child._source_position_and_key_path.source_position) == "<string>:2"  # noqa: SLF001 # type: ignore
