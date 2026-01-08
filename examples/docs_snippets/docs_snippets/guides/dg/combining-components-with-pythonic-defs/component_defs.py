from pathlib import Path

import dagster as dg


# start_resources
class MyResource(dg.ConfigurableResource): ...


def get_warehouse_resource():
    return MyResource()


# end_resources


# start_assets
@dg.asset
def customer_segmentation(warehouse: MyResource) -> None: ...


@dg.asset(deps=[customer_segmentation])
def revenue_forecast(warehouse: MyResource) -> None: ...


# end_assets


# start_definitions_simple
@dg.definitions
def defs():
    """Combine Components and Pythonic assets."""
    # Load component definitions from the defs/ folder
    component_defs = dg.load_from_defs_folder(path_within_project=Path(__file__).parent)

    # Create definitions for Pythonic assets
    pythonic_defs = dg.Definitions(
        assets=[customer_segmentation, revenue_forecast],
    )

    # Merge component definitions with pythonic definitions
    return dg.Definitions.merge(component_defs, pythonic_defs)


# end_definitions_simple


# start_definitions_with_resources
@dg.definitions
def defs():
    """Combine Components and Pythonic assets with shared resources."""
    # Load component definitions from the defs/ folder
    component_defs = dg.load_from_defs_folder(path_within_project=Path(__file__).parent)

    # Define resources available to ALL assets (components and pythonic)
    resources = {
        "warehouse": get_warehouse_resource(),
    }

    # Create definitions for Pythonic assets
    pythonic_defs = dg.Definitions(
        assets=[customer_segmentation, revenue_forecast],
        resources=resources,
    )

    # Merge component definitions with pythonic definitions
    return dg.Definitions.merge(component_defs, pythonic_defs)


# end_definitions_with_resources


# start_resources_in_defs
@dg.definitions
def defs():
    return dg.Definitions(
        resources={
            "warehouse": MyResource(),
        }
    )


# end_resources_in_defs
