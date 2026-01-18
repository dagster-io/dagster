from random import randint

import dagster as dg


class AssetWithSchedule(dg.Component, dg.Model, dg.Resolvable):
    asset_key: list[str]
    cron_schedule: str

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        @dg.asset(key=dg.AssetKey(self.asset_key))
        def asset():
            return randint(1, 100)

        schedule = dg.ScheduleDefinition(
            name=f"{'_'.join(self.asset_key)}_schedule",
            cron_schedule=self.cron_schedule,
            target=asset,
        )

        return dg.Definitions(assets=[asset], schedules=[schedule])
