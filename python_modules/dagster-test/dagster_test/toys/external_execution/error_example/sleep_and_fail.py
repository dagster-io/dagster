import time

from dagster_pipes import open_dagster_pipes

with open_dagster_pipes() as context:
    n = context.get_extra("sleep_seconds")
    context.log.info(f"sleeping for {n} seconds")
    time.sleep(n)
    raise Exception("oops all errors")
