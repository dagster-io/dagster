from pathlib import Path
from typing import Any, Callable, Optional

from dagster import AssetsDefinition, multi_asset
from dagster._annotations import experimental
from dagster._core.errors import DagsterInvariantViolationError

from .asset_utils import (
    build_looker_dashboard_specs,
    build_looker_explore_specs,
    build_looker_view_specs,
)
from .dagster_looker_translator import DagsterLookerTranslator


@experimental
def looker_assets(
    *,
    project_dir: Path,
    dagster_looker_translator: Optional[DagsterLookerTranslator] = None,
) -> Callable[[Callable[..., Any]], AssetsDefinition]:
    """A decorator for defining Looker assets in a project.

    Args:
        project_dir (Path): The path to the Looker project directory.

    Examples:
        .. code-block:: python

            from pathlib import Path

            from dagster_looker import looker_assets

            @looker_assets(project_dir=Path("my_looker_project"))
            def my_looker_project_assets(): ...
    """
    dagster_looker_translator = dagster_looker_translator or DagsterLookerTranslator()

    def looker_assets_as_external_assets(fn: Callable[..., Any]) -> AssetsDefinition:
        @multi_asset(
            name=fn.__name__,
            compute_kind="looker",
            specs=[
                *build_looker_dashboard_specs(project_dir, dagster_looker_translator),
                *build_looker_explore_specs(project_dir, dagster_looker_translator),
                *build_looker_view_specs(project_dir, dagster_looker_translator),
            ],
        )
        def _fn():
            raise DagsterInvariantViolationError(
                "You have attempted to execute an unexecutable asset computed from"
                f" {fn.__name__}."
            )

        return _fn

    return looker_assets_as_external_assets
