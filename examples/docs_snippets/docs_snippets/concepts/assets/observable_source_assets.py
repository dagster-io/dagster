def read_some_file():
    return "foo"


# ruff: isort: split
# start_plain
from hashlib import sha256

import dagster as dg


@dg.observable_source_asset
def foo_source_asset():  # type: ignore  # (didactic)
    content = read_some_file()
    hash_sig = sha256()
    hash_sig.update(bytearray(content, "utf8"))
    return dg.DataVersion(hash_sig.hexdigest())


# end_plain

# ruff: isort: split
# start_schedule
import dagster as dg


@dg.observable_source_asset
def foo_source_asset():
    content = read_some_file()
    hash_sig = sha256()
    hash_sig.update(bytearray(content, "utf8"))
    return dg.DataVersion(hash_sig.hexdigest())


observation_job = dg.define_asset_job("observation_job", [foo_source_asset])

# schedule that will run the observation on foo_source_asset every day
observation_schedule = dg.ScheduleDefinition(
    name="observation_schedule",
    cron_schedule="@daily",
    job=observation_job,
)
# end_schedule
