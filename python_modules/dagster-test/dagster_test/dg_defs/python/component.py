import dagster as dg
from dagster.components.lib.executable_component.function_component import FunctionComponent


def solo():
    return None


@dg.component_instance
def only(_):
    return FunctionComponent(
        execution=solo,
        assets=[dg.AssetSpec(key="solo_py")],
    )
