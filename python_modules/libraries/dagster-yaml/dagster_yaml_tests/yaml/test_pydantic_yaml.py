import pytest
from dagster_yaml.yaml.object_mapping import HasObjectMappingContext
from dagster_yaml.yaml.pydantic_yaml import parse_yaml_file
from pydantic import BaseModel, ValidationError


def test_pydantic_yaml_validation_error() -> None:
    class BrokenModel2(BaseModel):
        bar: str

    class BrokenModel(BaseModel):
        foo: list[BrokenModel2]

    with pytest.raises(ValidationError) as e:
        parse_yaml_file(BrokenModel, "foo:\n  - bar: 1")
    assert "foo.0.bar at <string>:2" in str(e)


def test_pydantic_yaml_smoke() -> None:
    class MyModel2(BaseModel, HasObjectMappingContext):
        name: str

    class MyModel(BaseModel):
        child: MyModel2

    rv = parse_yaml_file(MyModel, "child:\n  name: foo")
    assert rv.child.name == "foo"
    assert str(rv.child._object_mapping_context.source_position) == "<string>:2"  # noqa: SLF001 # type: ignore
