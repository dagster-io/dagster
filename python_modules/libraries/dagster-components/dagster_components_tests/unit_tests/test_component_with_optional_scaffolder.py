from typing import Union

from dagster_components import Component
from dagster_components.core.component import (
    ComponentScaffolder,
    ComponentScaffolderUnavailableReason,
)


class ComponentWithOptionalScaffolder(Component):
    @classmethod
    def get_scaffolder(cls) -> Union[ComponentScaffolder, ComponentScaffolderUnavailableReason]:
        # Check for some installed dependency
        # _has_dagster_dbt = importlib.util.find_spec("dagster_dbt") is not None
        return ComponentScaffolderUnavailableReason(
            "In order to scaffold this component you must install dagster_foobar with the [dev] extra. E.g. `uv add dagster-foobar[dev]` or `pip install dagster-foobar[dev]`"
        )


def test_component_with_optional_scaffolder() -> None:
    assert isinstance(
        ComponentWithOptionalScaffolder.get_scaffolder(), ComponentScaffolderUnavailableReason
    )
