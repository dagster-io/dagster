import dagster as dg


# start_scheduled_job_component
class ScheduledJobComponent(dg.Component, dg.Model, dg.Resolvable):
    """Schedule assets using flexible selection syntax."""

    job_name: str
    cron_schedule: str
    asset_selection: str

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        job = dg.define_asset_job(
            name=self.job_name,
            selection=self.asset_selection,
        )

        schedule = dg.ScheduleDefinition(
            job=job,
            cron_schedule=self.cron_schedule,
        )

        return dg.Definitions(
            schedules=[schedule],
            jobs=[job],
        )


# end_scheduled_job_component
