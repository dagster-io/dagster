from unittest.mock import patch

from dagster import build_init_resource_context
from dagster_wandb.resources import WANDB_CLOUD_HOST, wandb_resource

API_KEY = "api_key"
CUSTOM_HOST = "https://qa.platform.ai"


@patch("dagster_wandb.resources.Api")
@patch("dagster_wandb.resources.wandb")
def test_wandb_resource(wandb, api):
    init_context = build_init_resource_context(config={"api_key": API_KEY})
    assert wandb_resource(init_context) == {
        "sdk": wandb,
        "api": api.return_value,
        "host": WANDB_CLOUD_HOST,
    }
    wandb.login.assert_called_with(key=API_KEY, host=WANDB_CLOUD_HOST, anonymous="never")
    wandb.Settings.assert_called_with(
        api_key=API_KEY,
        base_url=WANDB_CLOUD_HOST,
        anonymous="never",
        launch=True,
    )
    api.assert_called_with(
        default_settings=wandb.Settings.return_value,
        load_settings=False,
    )


@patch("dagster_wandb.resources.Api")
@patch("dagster_wandb.resources.wandb")
def test_wandb_resource_custom_host(wandb, api):
    init_context = build_init_resource_context(config={"api_key": API_KEY, "host": CUSTOM_HOST})
    assert wandb_resource(init_context) == {
        "sdk": wandb,
        "api": api.return_value,
        "host": CUSTOM_HOST,
    }
    wandb.login.assert_called_with(key=API_KEY, host=CUSTOM_HOST, anonymous="never")
    wandb.Settings.assert_called_with(
        api_key=API_KEY,
        base_url=CUSTOM_HOST,
        anonymous="never",
        launch=True,
    )
    api.assert_called_with(
        default_settings=wandb.Settings.return_value,
        load_settings=False,
    )
