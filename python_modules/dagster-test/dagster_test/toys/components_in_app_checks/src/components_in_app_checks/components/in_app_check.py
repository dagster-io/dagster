import dagster as dg


class InAppCheck(dg.Component, dg.Model, dg.Resolvable):
    """Asset check defined in the app."""

    # added fields here will define params when instantiated in Python, and yaml schema via Resolvable
    name: str

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        # Add definition construction logic here.
        _in_app_checks = []

        @dg.asset_check(asset="always_materializes", name=self.name)
        def check_fn():
            return dg.AssetCheckResult(
                passed=True, asset_key="always_materializes", check_name=self.name
            )

        return dg.Definitions(asset_checks=[check_fn])
