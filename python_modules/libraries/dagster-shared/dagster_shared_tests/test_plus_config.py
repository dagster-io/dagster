from dagster_shared.plus.config import get_region_from_url


class TestGetRegionFromUrl:
    def test_eu_url_returns_eu(self):
        assert get_region_from_url("https://eu.dagster.cloud") == "eu"
        assert get_region_from_url("https://eu.dagster.cloud/myorg") == "eu"
        assert get_region_from_url("https://myorg.eu.dagster.cloud") == "eu"

    def test_us_url_returns_none(self):
        assert get_region_from_url("https://dagster.cloud") is None
        assert get_region_from_url("https://dagster.cloud/myorg") is None
        assert get_region_from_url("https://myorg.dagster.cloud") is None

    def test_none_url_returns_none(self):
        assert get_region_from_url(None) is None

    def test_empty_url_returns_none(self):
        assert get_region_from_url("") is None
