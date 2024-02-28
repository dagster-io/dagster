import pytest
from dagster_wandb.utils.errors import (
    WandbArtifactsIOManagerError,
    raise_on_empty_configuration,
    raise_on_unknown_keys,
)


def raise_on_unknown_keys_green_path():
    dictionary = {"version": "value", "get_path": "value"}
    raise_on_unknown_keys("partition", dictionary, True)


def raise_on_unknown_keys_red_path():
    dictionary = {"name ": "value", "path": "value"}

    with pytest.raises(WandbArtifactsIOManagerError):
        raise_on_unknown_keys("partition", dictionary, True)


def test_raise_on_empty_configuration():
    dictionary = {}
    with pytest.raises(WandbArtifactsIOManagerError):
        raise_on_empty_configuration("partition", dictionary)
