from dagster import asset

from .include_me import some_function  # noqa


@asset
def an_asset() -> None:
    some_function()
