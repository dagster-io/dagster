from typing import Annotated

from dagster_components.resolved.context import ResolutionContext
from dagster_components.resolved.model import Resolved, Resolver


def test_simple_dataclass_resolveable_from_model():
    from dataclasses import dataclass

    @dataclass
    class Hello(Resolved):
        hello: Annotated[
            int,
            Resolver.from_model(
                lambda context, m: int(m.hello),
                model_field_type=str,
            ),
        ]

    hello = Hello.resolve(
        ResolutionContext.default(),
        Hello.model()(hello="1"),
    )

    assert isinstance(hello, Hello)
    assert hello.hello == 1


def test_simple_pydantic_resolveable_from_schema():
    from pydantic import BaseModel

    class Hello(BaseModel, Resolved):
        hello: Annotated[
            int,
            Resolver(
                lambda context, v: int(v),
                model_field_type=str,
            ),
        ]

    hello = Hello.resolve(
        ResolutionContext.default(),
        Hello.model()(hello="1"),
    )

    assert isinstance(hello, Hello)
    assert hello.hello == 1


def test_simple_dataclass_resolveable_field():
    from dataclasses import dataclass

    @dataclass
    class Hello(Resolved):
        hello: Annotated[
            int,
            Resolver(
                lambda context, val: int(val),
                model_field_type=str,
            ),
        ]

    hello = Hello.resolve(
        ResolutionContext.default(),
        Hello.model()(hello="1"),
    )

    assert isinstance(hello, Hello)
    assert hello.hello == 1
