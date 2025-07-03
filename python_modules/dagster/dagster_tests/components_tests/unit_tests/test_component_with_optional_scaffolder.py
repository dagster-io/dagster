import dagster as dg
from dagster.components.component_scaffolding import get_scaffolder
from dagster.components.scaffold.scaffold import ScaffolderUnavailableReason


@dg.scaffold_with(
    ScaffolderUnavailableReason(
        "In order to scaffold this component you must install dagster_foobar with the [dev] extra. E.g. `uv add dagster-foobar[dev]` or `pip install dagster-foobar[dev]`"
    )
)
class ComponentWithOptionalScaffolder(dg.Component): ...


def test_component_with_optional_scaffolder() -> None:
    assert isinstance(
        get_scaffolder(ComponentWithOptionalScaffolder),
        ScaffolderUnavailableReason,
    )
