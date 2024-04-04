from dagster import Config, StaticPartitionsDefinition, asset


@asset
def asset1() -> None: ...


@asset(key_prefix=["some", "key", "prefix"])
def asset_with_prefix() -> None: ...


@asset(deps=[asset1])
def downstream_asset() -> None: ...


@asset(partitions_def=StaticPartitionsDefinition(["one", "two", "three"]))
def partitioned_asset() -> None: ...


@asset(partitions_def=StaticPartitionsDefinition(["apple", "banana", "pear"]))
def differently_partitioned_asset() -> None: ...

class MyConfig(Config):
    some_prop: str

@asset
def asset_with_config(config: MyConfig):
    return config.some_prop

@asset
def fail_asset() -> None:
    raise Exception("failure")
