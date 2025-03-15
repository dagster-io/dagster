from dagster_components import Component, ResolvableModel
from dagster_components.resolved.context import ResolutionContext


def test_basic_from_dict() -> None:
    class AComponent(Component, ResolvableModel):
        a: int
        b: str

        def build_defs(self, context): ...

    context = ResolutionContext.default()
    inst = AComponent.from_dict(context=context, attributes={"a": 1, "b": "test"})
    assert isinstance(inst, AComponent)
    assert inst.a == 1
    assert inst.b == "test"
