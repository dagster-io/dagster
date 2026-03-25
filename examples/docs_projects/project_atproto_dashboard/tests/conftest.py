from unittest.mock import patch


def pytest_configure(config):
    # Patch load_powerbi_asset_specs before dashboard.py is imported during defs loading.
    # The function makes live PowerBI API calls which are unavailable in test environments.
    patch("dagster_powerbi.load_powerbi_asset_specs", return_value=[]).start()
