from collections.abc import Mapping

from dagster_components import ComponentLoadContext
from dagster_components.core.resource_injection import resource_injector
from dagster_components_tests.integration_tests.some_resource import SomeResource


@resource_injector
def resources(context: ComponentLoadContext) -> Mapping[str, object]:
    """This component loads a Definitions object with no assets."""
    return {"some_resource": SomeResource("some_value")}
