from dagster_components import Component
from dagster_components.scaffold import get_scaffolder
from dagster_components.scaffoldable.registry import scaffoldable
from dagster_components.scaffoldable.scaffolder import ScaffolderUnavailableReason


@scaffoldable(
    scaffolder=ScaffolderUnavailableReason(
        "In order to scaffold this component you must install dagster_foobar with the [dev] extra. E.g. `uv add dagster-foobar[dev]` or `pip install dagster-foobar[dev]`"
    )
)
class ComponentWithOptionalScaffolder(Component): ...


def test_component_with_optional_scaffolder() -> None:
    assert isinstance(
        get_scaffolder(ComponentWithOptionalScaffolder),
        ScaffolderUnavailableReason,
    )
