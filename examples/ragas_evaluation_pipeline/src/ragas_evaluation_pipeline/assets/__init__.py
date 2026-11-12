"""Asset package — the 8-asset evaluation graph lives in :mod:`.pipeline`.

Definitions loads these via ``load_assets_from_modules([pipeline])``.
"""

from __future__ import annotations

from ragas_evaluation_pipeline.assets import pipeline

__all__ = ["pipeline"]
