# ruff: isort: skip_file

# start_op_job_group
import dagster as dg


@dg.op
def vacuum_warehouse(): ...


@dg.op
def rotate_credentials(): ...


@dg.job(group_name="operational")
def warehouse_vacuum_job():
    vacuum_warehouse()


@dg.job(group_name="operational")
def credential_rotation_job():
    rotate_credentials()


# end_op_job_group

# start_asset_job_group
import dagster as dg


@dg.asset
def customers(): ...


customers_job = dg.define_asset_job(
    name="customers_job",
    selection=dg.AssetSelection.assets(customers),
    group_name="analytics",
)
# end_asset_job_group

# start_nested_job_group
import dagster as dg


@dg.op
def send_digest(): ...


@dg.job(group_name="operational/notifications")
def daily_digest_job():
    send_digest()


# end_nested_job_group
