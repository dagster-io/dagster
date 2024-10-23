from dagster import AssetsDefinition, AutomationCondition, Definitions


def apply_eager_automation(defs: Definitions) -> Definitions:
    assets = []
    for asset in defs.assets or []:
        if not isinstance(asset, AssetsDefinition):
            continue
        if not asset.keys:
            continue
        assets.append(
            asset.map_asset_specs(
                lambda spec: spec._replace(automation_condition=AutomationCondition.eager())
                if spec.automation_condition is None
                else spec
            )
        )
    return Definitions(
        assets=assets,
        asset_checks=defs.asset_checks,
        sensors=defs.sensors,
        schedules=defs.schedules,
        resources=defs.resources,
    )
