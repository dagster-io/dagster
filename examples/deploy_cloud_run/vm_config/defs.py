from time import sleep

from dagster import asset


@asset()
def test():
    sleep(10)
    return 1
