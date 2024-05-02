import itertools
from pathlib import Path
from typing import Any, Callable

import yaml
from dagster import AssetKey, AssetsDefinition, AssetSpec, multi_asset


def looker_assets(*, project_dir: Path) -> Callable[[Callable[..., Any]], AssetsDefinition]:
    lookml_dashboard_specs = [
        AssetSpec(
            key=AssetKey(lookml_dashboard["dashboard"]),
            deps={AssetKey(dashboard_element["explore"])},
        )
        for dashboard_path in project_dir.rglob("*.dashboard.lookml")
        # Each dashboard file can contain multiple dashboards.
        for lookml_dashboard in yaml.safe_load(dashboard_path.read_bytes())
        # For each dashboard, we create an asset. An `explore` in the dashboard is a dependency.
        for dashboard_element in itertools.chain(
            lookml_dashboard.get("elements", []),
            lookml_dashboard.get("filters", []),
        )
        if dashboard_element.get("explore")
    ]

    return multi_asset(
        compute_kind="looker",
        specs=[
            *lookml_dashboard_specs,
        ],
    )
