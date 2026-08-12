"""Tests for the ``enable_contract_metadata`` opt-in that surfaces dbt model contract
info (``config.contract.enforced`` and column/model constraints) as spec metadata.

Contracts are surfaced as metadata rather than as Dagster asset checks because dbt
enforces contracts at model build time — a violation fails the whole materialization,
so there is no separate post-materialization pass/fail signal. That failure mode is
fundamentally different from Dagster asset checks (which are post-materialization
assertions with independent pass/fail results). Users who want per-column verification
should keep using explicit dbt tests, which ``dagster-dbt`` lifts into per-column
asset checks separately.
"""

from typing import Any

from dagster_dbt.asset_utils import (
    DAGSTER_DBT_COLUMN_CONSTRAINTS_METADATA_KEY,
    DAGSTER_DBT_CONTRACT_ENFORCED_METADATA_KEY,
    DAGSTER_DBT_MODEL_CONSTRAINTS_METADATA_KEY,
    default_contract_metadata_from_dbt_resource_props,
)
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator, DagsterDbtTranslatorSettings


class TestDefaultContractMetadataFromDbtResourceProps:
    """Unit tests for the pure helper — no manifest, no translator."""

    def _model(
        self,
        contract: dict[str, Any] | None = None,
        columns: dict[str, Any] | None = None,
        constraints: list[Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "resource_type": "model",
            "name": "my_model",
            "config": {"contract": contract} if contract else {},
            "columns": columns or {},
            "constraints": constraints or [],
        }

    def test_enforced_contract_produces_metadata(self) -> None:
        metadata = default_contract_metadata_from_dbt_resource_props(
            self._model(contract={"enforced": True})
        )
        assert metadata[DAGSTER_DBT_CONTRACT_ENFORCED_METADATA_KEY] is True
        assert metadata[DAGSTER_DBT_COLUMN_CONSTRAINTS_METADATA_KEY] == {}
        assert metadata[DAGSTER_DBT_MODEL_CONSTRAINTS_METADATA_KEY] == []

    def test_unenforced_contract_returns_empty(self) -> None:
        assert (
            default_contract_metadata_from_dbt_resource_props(
                self._model(contract={"enforced": False})
            )
            == {}
        )

    def test_missing_contract_returns_empty(self) -> None:
        assert default_contract_metadata_from_dbt_resource_props(self._model()) == {}

    def test_non_model_resource_returns_empty(self) -> None:
        for resource_type in ("source", "seed", "snapshot", "test"):
            props = {
                "resource_type": resource_type,
                "config": {"contract": {"enforced": True}},
            }
            assert default_contract_metadata_from_dbt_resource_props(props) == {}

    def test_column_constraints_captured(self) -> None:
        metadata = default_contract_metadata_from_dbt_resource_props(
            self._model(
                contract={"enforced": True},
                columns={
                    "id": {"constraints": [{"type": "not_null"}, {"type": "primary_key"}]},
                    "email": {"constraints": [{"type": "not_null"}]},
                    "created_at": {},  # column with no constraints — omitted from result
                },
            )
        )
        column_constraints = metadata[DAGSTER_DBT_COLUMN_CONSTRAINTS_METADATA_KEY]
        assert column_constraints == {
            "id": ["not_null", "primary_key"],
            "email": ["not_null"],
        }
        assert "created_at" not in column_constraints

    def test_model_constraints_passed_through(self) -> None:
        model_constraints_input = [
            {"type": "foreign_key", "columns": ["a"], "expression": "ref('x')"},
            {"type": "check", "expression": "a > 0"},
        ]
        metadata = default_contract_metadata_from_dbt_resource_props(
            self._model(contract={"enforced": True}, constraints=model_constraints_input)
        )
        assert metadata[DAGSTER_DBT_MODEL_CONSTRAINTS_METADATA_KEY] == model_constraints_input

    def test_constraint_without_type_ignored(self) -> None:
        # Guard against dbt YAML weirdness — a constraint dict without a ``type`` key
        # should be skipped rather than raising.
        metadata = default_contract_metadata_from_dbt_resource_props(
            self._model(
                contract={"enforced": True},
                columns={
                    "id": {"constraints": [{"type": "not_null"}, {"expression": "x > 0"}]},
                },
            )
        )
        assert metadata[DAGSTER_DBT_COLUMN_CONSTRAINTS_METADATA_KEY] == {"id": ["not_null"]}


class TestTranslatorContractMetadata:
    """Verify the translator's ``get_metadata`` merges contract metadata when the
    setting is enabled, and leaves the default metadata untouched when it's disabled.
    """

    def _contracted_model_props(self) -> dict[str, Any]:
        return {
            "resource_type": "model",
            "name": "dim_customer",
            "unique_id": "model.my_project.dim_customer",
            "config": {"contract": {"enforced": True}, "materialized": "table"},
            "columns": {
                "id": {"data_type": "bigint", "constraints": [{"type": "not_null"}]},
            },
            "constraints": [],
            "database": "db",
            "schema": "main",
            "alias": "dim_customer",
        }

    def test_default_translator_omits_contract_metadata(self) -> None:
        translator = DagsterDbtTranslator()  # enable_contract_metadata defaults to False
        metadata = translator.get_metadata(self._contracted_model_props())
        assert DAGSTER_DBT_CONTRACT_ENFORCED_METADATA_KEY not in metadata
        assert DAGSTER_DBT_COLUMN_CONSTRAINTS_METADATA_KEY not in metadata
        assert DAGSTER_DBT_MODEL_CONSTRAINTS_METADATA_KEY not in metadata

    def test_enabled_translator_includes_contract_metadata(self) -> None:
        translator = DagsterDbtTranslator(
            settings=DagsterDbtTranslatorSettings(enable_contract_metadata=True)
        )
        metadata = translator.get_metadata(self._contracted_model_props())
        assert metadata[DAGSTER_DBT_CONTRACT_ENFORCED_METADATA_KEY] is True
        assert metadata[DAGSTER_DBT_COLUMN_CONSTRAINTS_METADATA_KEY] == {"id": ["not_null"]}
        assert metadata[DAGSTER_DBT_MODEL_CONSTRAINTS_METADATA_KEY] == []

    def test_enabled_translator_preserves_default_metadata(self) -> None:
        translator = DagsterDbtTranslator(
            settings=DagsterDbtTranslatorSettings(enable_contract_metadata=True)
        )
        metadata = translator.get_metadata(self._contracted_model_props())
        # The default column_schema / table_name metadata should still be present.
        assert "dagster/column_schema" in metadata
        assert "dagster/table_name" in metadata
