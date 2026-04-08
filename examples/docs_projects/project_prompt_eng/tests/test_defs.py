from unittest.mock import MagicMock

import dagster as dg
from dagster import AssetKey
from project_prompt_eng.definitions import defs as _raw_defs
from project_prompt_eng.defs.assets import (
    InputLocation,
    UserInputSchema,
    available_fuel_stations,
    nearest_fuel_stations,
    user_input_prompt,
)

defs: dg.Definitions = _raw_defs() if not isinstance(_raw_defs, dg.Definitions) else _raw_defs


def test_defs_load():
    assert isinstance(defs, dg.Definitions)


def test_assets_defined():
    repo = defs.get_repository_def()
    asset_keys = set(repo.assets_defs_by_key.keys())
    assert AssetKey("user_input_prompt") in asset_keys
    assert AssetKey("nearest_fuel_stations") in asset_keys
    assert AssetKey("available_fuel_stations") in asset_keys


def _mock_anthropic(response_text: str) -> MagicMock:
    """Build a mock AnthropicResource whose client returns a fixed text response."""
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=response_text)]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message

    mock_cm = MagicMock()
    mock_cm.__enter__ = MagicMock(return_value=mock_client)
    mock_cm.__exit__ = MagicMock(return_value=False)

    mock_anthropic = MagicMock()
    mock_anthropic.get_client.return_value = mock_cm
    return mock_anthropic


def test_user_input_prompt_parses_location_and_fuel_type():
    response_json = '{"latitude": 37.7749, "longitude": -122.4194, "fuel_type": "ELEC"}'
    mock_anthropic = _mock_anthropic(response_json)

    context = dg.build_asset_context()
    config = InputLocation(location="San Francisco, CA with a Tesla Model 3")

    result = user_input_prompt(context, config, mock_anthropic)

    assert result.latitude == 37.7749
    assert result.longitude == -122.4194
    assert result.fuel_type == "ELEC"
    mock_anthropic.get_client.assert_called_once_with(context)


def test_user_input_prompt_passes_location_in_prompt():
    response_json = '{"latitude": 38.8977, "longitude": -77.0365, "fuel_type": "BD"}'
    mock_anthropic = _mock_anthropic(response_json)

    context = dg.build_asset_context()
    config = InputLocation(location="Washington DC with a biodiesel truck")

    user_input_prompt(context, config, mock_anthropic)

    call_args = (
        mock_anthropic.get_client.return_value.__enter__.return_value.messages.create.call_args
    )
    prompt_content = call_args.kwargs["messages"][0]["content"]
    assert "Washington DC with a biodiesel truck" in prompt_content


def test_nearest_fuel_stations_filters_stations_without_hours():
    mock_nrel = MagicMock()
    mock_nrel.alt_fuel_stations.return_value = [
        {"station_name": "All Day Station", "access_days_time": "24 hours daily"},
        {"station_name": "No Hours Station"},  # missing access_days_time
        {"station_name": "Weekday Station", "access_days_time": "M-F 8am-6pm"},
    ]

    user_input = UserInputSchema(latitude=37.7749, longitude=-122.4194, fuel_type="ELEC")
    stations = nearest_fuel_stations(mock_nrel, user_input)

    assert len(stations) == 2
    assert all("access_days_time" in s for s in stations)


def test_nearest_fuel_stations_caps_results_at_three():
    mock_nrel = MagicMock()
    mock_nrel.alt_fuel_stations.return_value = [
        {"station_name": f"Station {i}", "access_days_time": "24/7"} for i in range(10)
    ]

    user_input = UserInputSchema(latitude=37.7749, longitude=-122.4194, fuel_type="all")
    stations = nearest_fuel_stations(mock_nrel, user_input)

    assert len(stations) == 3


def test_nearest_fuel_stations_passes_correct_params_to_resource():
    mock_nrel = MagicMock()
    mock_nrel.alt_fuel_stations.return_value = []

    user_input = UserInputSchema(latitude=51.5074, longitude=-0.1278, fuel_type="BD")
    nearest_fuel_stations(mock_nrel, user_input)

    mock_nrel.alt_fuel_stations.assert_called_once_with(
        latitude=51.5074, longitude=-0.1278, fuel_type="BD"
    )


def test_available_fuel_stations_calls_anthropic_per_station():
    responses = ['{"is_open": true}', '{"is_open": false}', '{"is_open": true}']
    mock_message_seq = [MagicMock(content=[MagicMock(text=r)]) for r in responses]

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = mock_message_seq

    mock_cm = MagicMock()
    mock_cm.__enter__ = MagicMock(return_value=mock_client)
    mock_cm.__exit__ = MagicMock(return_value=False)

    mock_anthropic = MagicMock()
    mock_anthropic.get_client.return_value = mock_cm

    stations = [
        {
            "station_name": f"Station {i}",
            "street_address": f"{i} Main St",
            "distance": float(i),
            "access_days_time": "24/7",
        }
        for i in range(3)
    ]

    context = dg.build_asset_context()
    available_fuel_stations(context, mock_anthropic, stations)

    assert mock_client.messages.create.call_count == 3
