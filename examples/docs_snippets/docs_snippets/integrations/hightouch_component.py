from dagster_hightouch import ConfigurableHightouchResource, hightouch_sync_op

import dagster as dg

# start_job_example


@dg.job(
    resource_defs={
        "hightouch": ConfigurableHightouchResource(
            api_key=dg.EnvVar("HIGHTOUCH_API_KEY"),
        )
    }
)
def sync_job():
    hightouch_sync_op()


# end_job_example
