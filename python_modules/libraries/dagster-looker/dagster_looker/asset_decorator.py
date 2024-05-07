import itertools
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import lkml
import yaml
from dagster import AssetKey, AssetsDefinition, AssetSpec, multi_asset


def build_looker_explore_specs(project_dir: Path) -> Sequence[AssetSpec]:
    looker_explore_specs = []

    # https://cloud.google.com/looker/docs/reference/param-explore
    for model_path in project_dir.rglob("*.model.lkml"):
        for explore in lkml.load(model_path.read_text()).get("explores", []):
            explore_asset_key = AssetKey(["explore", explore["name"]])

            # https://cloud.google.com/looker/docs/reference/param-explore-from
            explore_base_view = [{"name": explore.get("from") or explore["name"]}]

            # https://cloud.google.com/looker/docs/reference/param-explore-join
            explore_join_views: Sequence[Mapping[str, Any]] = explore.get("joins", [])

            looker_explore_specs.append(
                AssetSpec(
                    key=explore_asset_key,
                    deps={
                        AssetKey(["view", view["name"]])
                        for view in itertools.chain(explore_base_view, explore_join_views)
                    },
                )
            )

    return looker_explore_specs


def build_looker_view_specs(project_dir: Path) -> Sequence[AssetSpec]:
    looker_view_specs = []

    # https://cloud.google.com/looker/docs/reference/param-view
    for view_path in project_dir.rglob("*.view.lkml"):
        for view in lkml.load(view_path.read_text()).get("views", []):
            upstream_table = view.get("sql_table_name") or view["name"]
            upstream_table_asset_key = AssetKey(upstream_table.replace("`", "").split("."))

            looker_view_specs.append(
                AssetSpec(
                    key=AssetKey(["view", view["name"]]),
                    deps={upstream_table_asset_key},
                )
            )

    return looker_view_specs


def looker_assets(*, project_dir: Path) -> Callable[[Callable[..., Any]], AssetsDefinition]:
    lookml_dashboard_specs = [
        AssetSpec(
            key=AssetKey(["dashboard", lookml_dashboard["dashboard"]]),
            deps={AssetKey(["explore", dashboard_element["explore"]])},
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
            *build_looker_explore_specs(project_dir),
            *build_looker_view_specs(project_dir),
        ],
    )
