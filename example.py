from dagster import job
from dagster_airbyte import airbyte_resource, airbyte_sync_op

my_airbyte_resource = airbyte_resource.configured(
    {
        "host": {"env": "localhost"},
        "port": {"env": "8000"},
    }
)

sync_foobar = airbyte_sync_op.configured({"connection_id": "7030bab3-8733-4f67-b1a3-3b7eacf362fa"}, name="sync_foobar")

@job(resource_defs={"fivetran": my_airbyte_resource})
def my_simple_airbyte_job():
    sync_foobar()
