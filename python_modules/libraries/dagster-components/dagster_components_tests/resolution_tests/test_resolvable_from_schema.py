from typing import Annotated

from dagster_components.core.schema.context import ResolutionContext
from dagster_components.core.schema.resolvable_from_schema import (
    FieldResolver,
    ResolvableModel,
    ResolvedFrom,
    resolve_schema_to_resolvable,
)


def test_simple_dataclass_resolveable_from_schema():
    class HelloSchema(ResolvableModel):
        hello: str

    from dataclasses import dataclass

    @dataclass
    class Hello(ResolvedFrom[HelloSchema]):
        hello: Annotated[int, FieldResolver.from_model(lambda context, schema: int(schema.hello))]

    hello = resolve_schema_to_resolvable(HelloSchema(hello="1"), Hello, ResolutionContext.default())

    assert isinstance(hello, Hello)
    assert hello.hello == 1


def test_simple_pydantic_resolveable_from_schema():
    class HelloSchema(ResolvableModel):
        hello: str

    from pydantic import BaseModel

    class Hello(BaseModel, ResolvedFrom[HelloSchema]):
        hello: Annotated[int, FieldResolver.from_model(lambda context, schema: int(schema.hello))]

    hello = resolve_schema_to_resolvable(HelloSchema(hello="1"), Hello, ResolutionContext.default())

    assert isinstance(hello, Hello)
    assert hello.hello == 1


def test_simple_dataclass_resolveable_from_schema_with_condense_syntax():
    class HelloSchema(ResolvableModel):
        hello: str

    from dataclasses import dataclass

    @dataclass
    class Hello(ResolvedFrom[HelloSchema]):
        hello: Annotated[int, FieldResolver(lambda context, val: int(val))]

    hello = resolve_schema_to_resolvable(HelloSchema(hello="1"), Hello, ResolutionContext.default())

    assert isinstance(hello, Hello)
    assert hello.hello == 1
