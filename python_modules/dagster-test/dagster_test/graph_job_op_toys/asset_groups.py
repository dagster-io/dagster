# pylint: disable=redefined-outer-name

from dagster import (
    AssetKey,
    IOManager,
    SourceAsset,
    asset,
    io_manager,
)


class MyIOManager(IOManager):
    def handle_output(self, context, obj):
        pass

    def load_input(self, context):
        return 5


@io_manager
def the_manager():
    return MyIOManager()


@asset(group_name="earth")
def grass():
    return 1


@asset(group_name="earth")
def tree(grass):
    return 1


river = SourceAsset(key=AssetKey('river'), group_name="water", io_manager_def=the_manager)


@asset(group_name="water")
def pond(river):
    return 1


@asset(group_name="water")
def ocean(pond):
    return 1


@asset(group_name="air")
def sky():
    return 1
