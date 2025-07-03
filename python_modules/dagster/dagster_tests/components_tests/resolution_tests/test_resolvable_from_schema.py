from typing import Annotated

import dagster as dg
from dagster import Resolver
from dagster.components.resolved.context import ResolutionContext


def test_simple_dataclass_resolveable_from_model():
    from dataclasses import dataclass

    @dataclass
    class Hello(dg.Resolvable):
        hello: Annotated[
            int,
            Resolver.from_model(
                lambda context, m: int(m.hello),
                model_field_type=str,
            ),
        ]

    hello = Hello.resolve_from_model(
        ResolutionContext.default(),
        Hello.model()(hello="1"),
    )

    assert isinstance(hello, Hello)
    assert hello.hello == 1


def test_simple_pydantic_resolveable_from_schema():
    from pydantic import BaseModel

    class Hello(BaseModel, dg.Resolvable):
        hello: Annotated[
            int,
            dg.Resolver(
                lambda context, v: int(v),
                model_field_type=str,
            ),
        ]

    hello = Hello.resolve_from_model(
        ResolutionContext.default(),
        Hello.model()(hello="1"),
    )

    assert isinstance(hello, Hello)
    assert hello.hello == 1


def test_simple_dataclass_resolveable_field():
    from dataclasses import dataclass

    @dataclass
    class Hello(dg.Resolvable):
        hello: Annotated[
            int,
            dg.Resolver(
                lambda context, val: int(val),
                model_field_type=str,
            ),
        ]

    hello = Hello.resolve_from_model(
        ResolutionContext.default(),
        Hello.model()(hello="1"),
    )

    assert isinstance(hello, Hello)
    assert hello.hello == 1
