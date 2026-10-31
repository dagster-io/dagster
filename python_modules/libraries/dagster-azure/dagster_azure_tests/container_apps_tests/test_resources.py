import pytest
from dagster_azure.container_apps.resources import (
    interpret_aca_cpu_str_as_millicpus,
    interpret_aca_mem_str_as_bytes,
)

KIB = 1024
MIB = KIB**2
GIB = KIB**3


class TestMemParser:
    def test_none_returns_none(self):
        assert interpret_aca_mem_str_as_bytes(None) is None

    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("1Gi", GIB),
            ("0.5Gi", GIB // 2),
            ("1.5Gi", int(1.5 * GIB)),
            ("4Gi", 4 * GIB),
            ("512Mi", 512 * MIB),
            ("0.25Mi", MIB // 4),
            ("1024Ki", 1024 * KIB),
            ("1Ki", KIB),
            ("2048", 2048),
            ("0", 0),
            (" 1Gi ", GIB),
            ("\t512Mi\n", 512 * MIB),
        ],
    )
    def test_known_suffixes(self, raw, expected):
        assert interpret_aca_mem_str_as_bytes(raw) == expected

    @pytest.mark.parametrize(
        "raw",
        ["1Gbz", "1G", "1M", "1gi", "1GiB", "Gi", "", "  ", "abc", "1,024Mi", "1Gi1Gi"],
    )
    def test_unrecognized_input_raises(self, raw):
        with pytest.raises(ValueError):
            interpret_aca_mem_str_as_bytes(raw)


class TestCpuParser:
    def test_none_returns_none(self):
        assert interpret_aca_cpu_str_as_millicpus(None) is None

    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("1", 1000),
            ("1.0", 1000),
            ("0.5", 500),
            ("0.25", 250),
            ("2", 2000),
            ("4.0", 4000),
            ("500m", 500),
            ("1000m", 1000),
            ("250m", 250),
            ("0m", 0),
            ("0", 0),
            (" 0.25 ", 250),
            ("\t500m\n", 500),
        ],
    )
    def test_parses(self, raw, expected):
        assert interpret_aca_cpu_str_as_millicpus(raw) == expected

    @pytest.mark.parametrize("raw", ["banana", "", "  ", "m", "1 core", "0.5M", "1,5"])
    def test_unrecognized_input_raises(self, raw):
        with pytest.raises(ValueError):
            interpret_aca_cpu_str_as_millicpus(raw)
