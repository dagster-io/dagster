from dagster_components import Component
from dagster_components.core.component import scaffolder_from_component_type
from dagster_components.scaffoldable.decorator import scaffoldable
from dagster_components.scaffoldable.scaffolder import ScaffolderUnavailableReason


@scaffoldable(
    scaffolder=ScaffolderUnavailableReason(
        "In order to scaffold this component you must install dagster_foobar with the [dev] extra. E.g. `uv add dagster-foobar[dev]` or `pip install dagster-foobar[dev]`"
    )
)
class ComponentWithOptionalScaffolder(Component): ...


def test_component_with_optional_scaffolder() -> None:
    assert isinstance(
        scaffolder_from_component_type(ComponentWithOptionalScaffolder),
        ScaffolderUnavailableReason,
    )
