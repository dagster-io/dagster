import sys
from unittest.mock import MagicMock, patch

import pytest
from dagster import build_init_resource_context
from dagster_wandb.resources import WANDB_CLOUD_HOST, wandb_resource

API_KEY = "api_key"
CUSTOM_HOST = "https://qa.platform.ai"
CONFIGS = [
    ({"api_key": API_KEY}, WANDB_CLOUD_HOST),
    ({"api_key": API_KEY, "host": CUSTOM_HOST}, CUSTOM_HOST),
]


@pytest.fixture
def launch_api():
    """Simulate wandb>=0.30, which provides wandb.sdk.launch.api.LaunchApi."""
    module = MagicMock()
    with patch.dict(sys.modules, {"wandb.sdk.launch.api": module}):
        yield module.LaunchApi


@pytest.fixture
def internal_api():
    """Simulate wandb<0.30, which has no LaunchApi but has the internal API client."""
    module = MagicMock()
    with patch.dict(
        sys.modules,
        {"wandb.sdk.launch.api": None, "wandb.sdk.internal.internal_api": module},
    ):
        yield module.Api


@pytest.mark.parametrize(("config", "host"), CONFIGS)
@patch("dagster_wandb.resources.wandb")
def test_wandb_resource(wandb, launch_api, config, host):
    init_context = build_init_resource_context(config=config)
    assert wandb_resource(init_context) == {
        "sdk": wandb,
        "api": launch_api.return_value,
        "host": host,
    }
    wandb.login.assert_called_with(key=API_KEY, host=host, anonymous="never")
    launch_api.assert_called_once_with(overrides={"base_url": host}, api_key=API_KEY)


@pytest.mark.parametrize(("config", "host"), CONFIGS)
@patch("dagster_wandb.resources.wandb")
def test_wandb_resource_before_wandb_0_30(wandb, internal_api, config, host):
    init_context = build_init_resource_context(config=config)
    assert wandb_resource(init_context) == {
        "sdk": wandb,
        "api": internal_api.return_value,
        "host": host,
    }
    wandb.login.assert_called_with(key=API_KEY, host=host, anonymous="never")
    wandb.Settings.assert_called_with(
        api_key=API_KEY,
        base_url=host,
        anonymous="never",
        launch=True,
    )
    internal_api.assert_called_with(
        default_settings=wandb.Settings.return_value,
        load_settings=False,
    )
