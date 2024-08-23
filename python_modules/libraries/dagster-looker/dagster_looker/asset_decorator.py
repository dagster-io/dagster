from pathlib import Path
from typing import Any, Callable, Optional

from dagster import (
    AssetsDefinition,
    PartitionsDefinition,
    _check as check,
    multi_asset,
)

from .asset_specs import build_looker_asset_specs
from .dagster_looker_translator import DagsterLookerTranslator


def looker_assets(
    *,
    project_dir: Path,
    name: Optional[str] = None,
    dagster_looker_translator: Optional[DagsterLookerTranslator] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
) -> Callable[[Callable[..., Any]], AssetsDefinition]:
    dagster_looker_translator = check.inst_param(
        dagster_looker_translator or DagsterLookerTranslator(),
        "dagster_looker_translator",
        DagsterLookerTranslator,
        )
    return multi_asset(
        name=name,
        compute_kind="looker",
        can_subset=True,
        partitions_def=partitions_def,
        specs=build_looker_asset_specs(
            project_dir=project_dir,
            dagster_looker_translator=dagster_looker_translator,
        ),
    )