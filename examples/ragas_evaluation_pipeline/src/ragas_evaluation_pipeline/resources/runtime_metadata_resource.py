"""RuntimeMetadataResource — configurable lineage tags (Point 7).

Provides model_name, embedding_model, index_version, prompt_version, and the
active ``scorer`` mode so every run is auditable. Exposed as a Dagster resource
so the values are configurable per run and recorded in materialization metadata.

Not carried here: corpus_hash, dataset_id, dataset_semver (derived from the
data files inside the dataset asset) and evaluation_timestamp (stamped at run
time in the summary asset).
"""

from __future__ import annotations

from dagster import ConfigurableResource


class RuntimeMetadataResource(ConfigurableResource):
    """Lineage/config values attached to metric and summary assets."""

    model_name: str = "simulated-extractive-qa"
    embedding_model: str = "keyword-overlap-v0"
    index_version: str = "idx-2026-06-01"
    prompt_version: str = "prompt-v1"
    scorer: str = "deterministic"  # or "ragas" (opt-in, needs an API key)

    def as_tags(self) -> dict:
        """Flatten to a plain string dict suitable for Dagster metadata/tags."""
        return {
            "model_name": self.model_name,
            "embedding_model": self.embedding_model,
            "index_version": self.index_version,
            "prompt_version": self.prompt_version,
            "scorer": self.scorer,
        }
