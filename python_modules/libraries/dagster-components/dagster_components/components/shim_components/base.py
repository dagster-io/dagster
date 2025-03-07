from dagster_components import Component


class ShimComponent(Component):
    """A component that will never be loaded independently. This exists purely as a vessel
    for the @scaffoldable decorator so that the dagster-dg CLI can know about and invoke
    commands against it. In the near future, we'll improve the CLI such that it can handle
    arbitrary scaffoldable objects so that this hack is no longer necessary.
    """

    def build_defs(self, context):
        raise NotImplementedError("Shim components should never be loaded.")
