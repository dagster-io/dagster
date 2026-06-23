from __future__ import annotations

from typing import Any

import dagster as dg
import pandas as pd


def add_dataframe_preview_metadata(
    context: dg.AssetExecutionContext,
    dataframe: pd.DataFrame,
    *,
    preview_rows: int = 5,
) -> pd.DataFrame:
    preview = dataframe.head(preview_rows).copy().astype(object)
    for column in preview.columns:
        preview[column] = preview[column].map(_normalize_metadata_value)

    preview_text = preview.to_string(index=False) if not preview.empty else "(no rows)"
    context.add_output_metadata(
        {
            "row_count": len(dataframe),
            "top_5_rows": dg.MetadataValue.md(f"```text\n{preview_text}\n```"),
        }
    )
    return dataframe


def _normalize_metadata_value(value: Any) -> Any:
    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    try:
        if bool(pd.isna(value)):
            return None
    except (TypeError, ValueError):
        pass

    if hasattr(value, "item") and callable(value.item):
        try:
            return value.item()
        except (TypeError, ValueError):
            pass

    return value
