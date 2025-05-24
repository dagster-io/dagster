"""Testing utilities for components."""

from collections.abc import Mapping
from typing import Any, Optional

from dagster._core.definitions.definitions_class import Definitions
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentLoadContext


def component_defs(
    *,
    component: Component,
    resources: Optional[Mapping[str, Any]] = None,
    context: Optional[ComponentLoadContext] = None,
) -> Definitions:
    """Builds a Definitions object from a Component.


    Args:
        component (Component): The Component to build the Definitions from.
        resources (Optional[Mapping[str, Any]]): A dictionary of resources to pass to the Component.
        context (Optional[ComponentLoadContext]): A ComponentLoadContext to pass to the Component. Defaults to a test context.

    Examples:

        .. code-block:: python

            # SimpleComponent produces an asset "an_asset"
            an_asset = component_defs(component=SimpleComponent()).get_assets_def("an_asset")
            assert an_asset.key == AssetKey("an_asset")

        .. code-block:: python

            # RequiresResoureComponent produces an asset "an_asset" and requires a resource "my_resource"
            an_asset = component_defs(
                component=SimpleComponent(),
                resources={"my_resource": MyResource()},
            ).get_assets_def("an_asset")
            assert an_asset.key == AssetKey("an_asset")
    """
    context = context or ComponentLoadContext.for_test()
    return component.build_defs(context).with_resources(resources)
