import os

from dagster_hightouch.ops import hightouch_sync_op
from dagster_hightouch.resources import ht_resource

import dagster as dg

HT_ORG = "39619"

run_ht_sync_orgs = hightouch_sync_op.configured(
    {"sync_id": HT_ORG}, name="hightouch_sfdc_organizations"
)


@dg.job
def ht_sfdc_job():
    ht_orgs = run_ht_sync_orgs()


defs = dg.Definitions(
    jobs=[ht_sfdc_job],
    resources={
        "hightouch": ht_resource.configured(
            {"api_key": dg.EnvVar("HIGHTOUCH_API_KEY")},
        ),
    },
)
