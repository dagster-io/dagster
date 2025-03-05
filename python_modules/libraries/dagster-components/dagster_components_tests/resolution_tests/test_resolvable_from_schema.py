from typing import Annotated

from dagster_components.core.schema.context import ResolutionContext
from dagster_components.core.schema.resolvable_from_schema import (
    ResolvableFromSchema,
    YamlFieldResolver,
    YamlSchema,
    resolve_schema_to_resolvable,
)


def test_simple_dataclass_resolveable_from_schema():
    class HelloSchema(YamlSchema):
        hello: str

    from dataclasses import dataclass

    @dataclass
    class Hello(ResolvableFromSchema[HelloSchema]):
        hello: Annotated[
            int, YamlFieldResolver.from_parent(lambda context, schema: int(schema.hello))
        ]

    hello = resolve_schema_to_resolvable(HelloSchema(hello="1"), Hello, ResolutionContext.default())

    assert isinstance(hello, Hello)
    assert hello.hello == 1


def test_simple_pydantic_resolveable_from_schema():
    class HelloSchema(YamlSchema):
        hello: str

    from pydantic import BaseModel

    class Hello(BaseModel, ResolvableFromSchema[HelloSchema]):
        hello: Annotated[
            int, YamlFieldResolver.from_parent(lambda context, schema: int(schema.hello))
        ]

    hello = resolve_schema_to_resolvable(HelloSchema(hello="1"), Hello, ResolutionContext.default())

    assert isinstance(hello, Hello)
    assert hello.hello == 1


def test_simple_dataclass_resolveable_from_schema_with_condense_syntax():
    class HelloSchema(YamlSchema):
        hello: str

    from dataclasses import dataclass

    @dataclass
    class Hello(ResolvableFromSchema[HelloSchema]):
        hello: Annotated[int, YamlFieldResolver(lambda context, val: int(val))]

    hello = resolve_schema_to_resolvable(HelloSchema(hello="1"), Hello, ResolutionContext.default())

    assert isinstance(hello, Hello)
    assert hello.hello == 1
