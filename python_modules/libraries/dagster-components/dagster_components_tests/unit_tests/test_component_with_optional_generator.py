from typing import Union

from dagster_components import Component
from dagster_components.core.component import (
    ComponentGenerator,
    ComponentGeneratorUnavailableReason,
)


class ComponentWithOptionalGenerator(Component):
    @classmethod
    def get_generator(cls) -> Union[ComponentGenerator, ComponentGeneratorUnavailableReason]:
        # Check for some installed dependency
        # _has_dagster_dbt = importlib.util.find_spec("dagster_dbt") is not None
        return ComponentGeneratorUnavailableReason(
            "In order to generate this component you must install dagster_foobar with the [dev] extra. E.g. `uv add dagster-foobar[dev]` or `pip install dagster-foobar[dev]`"
        )


def test_component_with_optional_generator() -> None:
    assert isinstance(
        ComponentWithOptionalGenerator.get_generator(), ComponentGeneratorUnavailableReason
    )
