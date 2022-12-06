# start
from datetime import datetime
from dagster import LogicalVersion, observable_source_asset

@observable_source_asset
def foo_source_asset():
  return LogicalVersion(str(datetime.now()))
# end
