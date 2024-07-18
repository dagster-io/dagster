from pathlib import Path

from dagster_sdf.information_schema import SdfInformationSchema

from .sdf_workspaces import lineage_path


def test_info_schema_is_hydrated(lineage_target_dir: Path) -> None:
    information_schema = SdfInformationSchema(lineage_path, lineage_target_dir)
    assert information_schema.is_hydrated()


def test_info_schema_dependencies(lineage_target_dir: Path) -> None:
    information_schema = SdfInformationSchema(lineage_path, lineage_target_dir)

    assert information_schema.get_dependencies() == {
        "lineage.pub.knis": (["lineage.pub.middle"], []),
        "lineage.pub.middle": (["lineage.pub.source"], ["lineage.pub.knis", "lineage.pub.sink"]),
        "lineage.pub.sink": (["lineage.pub.middle"], []),
        "lineage.pub.source": ([], ["lineage.pub.middle"]),
    }
