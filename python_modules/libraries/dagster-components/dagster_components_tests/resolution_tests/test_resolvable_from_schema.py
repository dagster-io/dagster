from typing import Annotated

from dagster_components.resolved.context import ResolutionContext
from dagster_components.resolved.model import ResolvableModel, ResolvedFrom, Resolver, resolve_model


def test_simple_dataclass_resolveable_from_schema():
    class HelloModel(ResolvableModel):
        hello: str

    from dataclasses import dataclass

    @dataclass
    class Hello(ResolvedFrom[HelloModel]):
        hello: Annotated[int, Resolver.from_model(lambda context, schema: int(schema.hello))]

    hello = resolve_model(HelloModel(hello="1"), Hello, ResolutionContext.default())

    assert isinstance(hello, Hello)
    assert hello.hello == 1


def test_simple_pydantic_resolveable_from_schema():
    class HelloModel(ResolvableModel):
        hello: str

    from pydantic import BaseModel

    class Hello(BaseModel, ResolvedFrom[HelloModel]):
        hello: Annotated[int, Resolver.from_model(lambda context, schema: int(schema.hello))]

    hello = resolve_model(HelloModel(hello="1"), Hello, ResolutionContext.default())

    assert isinstance(hello, Hello)
    assert hello.hello == 1


def test_simple_dataclass_resolveable_from_schema_with_condense_syntax():
    class HelloModel(ResolvableModel):
        hello: str

    from dataclasses import dataclass

    @dataclass
    class Hello(ResolvedFrom[HelloModel]):
        hello: Annotated[int, Resolver(lambda context, val: int(val))]

    hello = resolve_model(HelloModel(hello="1"), Hello, ResolutionContext.default())

    assert isinstance(hello, Hello)
    assert hello.hello == 1
