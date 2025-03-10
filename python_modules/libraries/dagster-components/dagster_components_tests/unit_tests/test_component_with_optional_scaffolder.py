from dagster_components import Component
from dagster_components.blueprint import BlueprintUnavailableReason, blueprint
from dagster_components.component_scaffolding import get_blueprint


@blueprint(
    blueprint_cls=BlueprintUnavailableReason(
        "In order to scaffold this component you must install dagster_foobar with the [dev] extra. E.g. `uv add dagster-foobar[dev]` or `pip install dagster-foobar[dev]`"
    )
)
class ComponentWithOptionalScaffolder(Component): ...


def test_component_with_optional_blueprint() -> None:
    assert isinstance(
        get_blueprint(ComponentWithOptionalScaffolder),
        BlueprintUnavailableReason,
    )
