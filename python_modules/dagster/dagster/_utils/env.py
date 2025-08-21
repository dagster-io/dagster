import os

from dagster_shared.utils import environ as environ


def using_dagster_dev() -> bool:
    return bool(os.getenv("DAGSTER_IS_DEV_CLI"))


def use_verbose() -> bool:
    return bool(os.getenv("DAGSTER_verbose", "1"))
