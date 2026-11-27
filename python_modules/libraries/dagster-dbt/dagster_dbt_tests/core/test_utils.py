import json
from pathlib import Path
from unittest import mock

import pytest
from dagster_dbt.errors import DagsterDbtCoreNotInstalledError
from dagster_dbt.utils import select_unique_ids

CLOUD_MANIFEST_PATH = Path(__file__).parents[1] / "cloud_v2" / "manifest.json"


def test_select_unique_ids_without_dbt_core() -> None:
    """Selection with no dbt-core and no project.

    The default selection is every node in the manifest, which needs no selection engine —
    this is what keeps the dbt Cloud integration working without dbt-core. Anything else
    must fail with an error that says how to install dbt-core.
    """
    manifest = json.loads(CLOUD_MANIFEST_PATH.read_text())

    with mock.patch("dagster_dbt.utils.DBT_PYTHON_VERSION", None):
        for select in ("fqn:*", ""):
            assert (
                select_unique_ids(
                    select=select, exclude="", selector="", project=None, manifest_json=manifest
                )
                == manifest["nodes"].keys()
            )

        for select, exclude, selector in (
            ("tag:foo", "", ""),
            ("fqn:*", "tag:foo", ""),
            ("fqn:*", "", "my_selector"),
        ):
            with pytest.raises(DagsterDbtCoreNotInstalledError, match=r"dagster-dbt\[dbt-core\]"):
                select_unique_ids(
                    select=select,
                    exclude=exclude,
                    selector=selector,
                    project=None,
                    manifest_json=manifest,
                )


def test_select_unique_ids_default_matches_dbt_core() -> None:
    """The no-dbt-core fast path must agree with what dbt-core's selector returns."""
    pytest.importorskip("dbt.version")

    manifest = json.loads(CLOUD_MANIFEST_PATH.read_text())
    from_dbt_core = select_unique_ids(
        select="fqn:*", exclude="", selector="", project=None, manifest_json=manifest
    )
    with mock.patch("dagster_dbt.utils.DBT_PYTHON_VERSION", None):
        without_dbt_core = select_unique_ids(
            select="fqn:*", exclude="", selector="", project=None, manifest_json=manifest
        )

    assert from_dbt_core == without_dbt_core


def test_select_all_on_fusion_keeps_isolated_nodes() -> None:
    """A Fusion project's default selection comes from the manifest, not from `dbt list`.

    Fusion leaves a node with neither parents nor children out of the graph `dbt list` walks,
    so shelling out would silently drop it from the asset graph.
    """
    manifest = json.loads(CLOUD_MANIFEST_PATH.read_text())
    manifest["metadata"]["dbt_version"] = "2.0.6"
    isolated = "model.jaffle_shop.isolated"
    manifest["nodes"][isolated] = {
        "unique_id": isolated,
        "name": "isolated",
        "resource_type": "model",
        "config": {"materialized": "table"},
        "depends_on": {"nodes": []},
    }

    project = mock.MagicMock()
    with (
        mock.patch("dagster_dbt.utils.DBT_PYTHON_VERSION", None),
        mock.patch("dagster_dbt.utils._select_unique_ids_from_cli") as from_cli,
    ):
        selected = select_unique_ids(
            select="fqn:*", exclude="", selector="", project=project, manifest_json=manifest
        )

    assert isolated in selected
    assert selected == manifest["nodes"].keys()
    from_cli.assert_not_called()
