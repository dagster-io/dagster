import time

from dagster import asset

print("WAITING 10 seconds")  # noqa
time.sleep(10)
print("DONE WAITING")  # noqa


@asset
def my_asset():
    pass
