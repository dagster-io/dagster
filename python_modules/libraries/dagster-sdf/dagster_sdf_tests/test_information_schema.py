from pathlib import Path
from dagster_sdf.sdf_information_schema import SdfInformationSchema
from .sdf_workspaces import test_csv_123_path


def test_info_schema_is_hydrated(
    test_csv_123_target_dir: Path
) -> None:
    information_schema = SdfInformationSchema(test_csv_123_path, test_csv_123_target_dir)
    assert information_schema.is_hydrated()

def test_info_schema_dependencies(
    test_csv_123_target_dir: Path
) -> None:
    information_schema = SdfInformationSchema(test_csv_123_path, test_csv_123_target_dir)
    assert information_schema.get_dependencies() == {
        "csv_123.pub.one": ([], ["csv_123.pub.two"]),
        "csv_123.pub.two": (["csv_123.pub.one"], ["csv_123.pub.three"]),
        "csv_123.pub.three": (["csv_123.pub.two"], [])
    }