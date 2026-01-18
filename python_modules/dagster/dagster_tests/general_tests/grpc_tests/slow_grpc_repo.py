import time

import dagster as dg

print("WAITING 10 seconds")  # noqa
time.sleep(10)
print("DONE WAITING")  # noqa


@dg.asset
def my_asset():
    pass
