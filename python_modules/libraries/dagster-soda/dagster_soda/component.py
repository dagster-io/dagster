import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Optional

import yaml
from dagster import (
    AssetCheckResult,
    AssetCheckSpec,
    AssetKey,
    Definitions,
    MetadataValue,
    multi_asset_check,
)
from dagster._core.definitions.asset_checks.asset_checks_definition import AssetChecksDefinition
from dagster._core.execution.context.asset_check_execution_context import AssetCheckExecutionContext
from dagster.components import Component, ComponentLoadContext, Model, Resolvable
from dagster.components.scaffold.scaffold import scaffold_with
from pydantic import Field
from soda.scan import Scan

from dagster_soda.scaffolder import SodaScanComponentScaffolder

SODACL_CHECKS_FOR_PREFIX = "checks for "
# Characters invalid in Dagster check names
INVALID_CHECK_NAME_CHARS = re.compile(r"[^a-zA-Z0-9_]")


def _sanitize_check_name(name: str) -> str:
    """Convert a string to a valid Dagster check name."""
    return INVALID_CHECK_NAME_CHARS.sub("_", name)[:100].strip("_") or "check"


def _add_configuration(scan: Any, config_path: str) -> None:
    """Add configuration to scan - supports both soda-core v3 and v4 API."""
    if hasattr(scan, "add_configuration_yaml_file"):
        scan.add_configuration_yaml_file(config_path)
    elif hasattr(scan, "add_configuration"):
        scan.add_configuration(file_path=config_path)
    else:
        raise AttributeError("Scan has neither add_configuration_yaml_file nor add_configuration")


def _add_sodacl_file(scan: Any, checks_path: str) -> None:
    """Add SodaCL YAML file to scan - supports both soda-core v3 and v4 API."""
    if hasattr(scan, "add_sodacl_yaml_file"):
        scan.add_sodacl_yaml_file(checks_path)
    elif hasattr(scan, "add_sodacl"):
        scan.add_sodacl(file_path=checks_path)
    else:
        raise AttributeError("Scan has neither add_sodacl_yaml_file nor add_sodacl")


def _parse_check_identifiers_from_yaml(yaml_path: Path, dataset: str) -> list[str]:
    """Extract individual check identifiers for a dataset from a SodaCL YAML file."""
    content = yaml_path.read_text()
    parsed = yaml.safe_load(content) or {}
    key = f"{SODACL_CHECKS_FOR_PREFIX}{dataset}"
    if key not in parsed:
        return []

    checks_raw = parsed[key]
    if not isinstance(checks_raw, list):
        return []

    identifiers: list[str] = []
    for i, item in enumerate(checks_raw):
        if isinstance(item, dict):
            for check_def, config in item.items():
                if isinstance(config, dict) and "name" in config:
                    identifiers.append(_sanitize_check_name(str(config["name"])))
                else:
                    identifiers.append(_sanitize_check_name(str(check_def)) or f"soda_{i}")
                break
        elif isinstance(item, str):
            identifiers.append(_sanitize_check_name(item) or f"soda_{i}")
        else:
            identifiers.append(f"soda_{i}")

    seen: set[str] = set()
    deduped: list[str] = []
    for base_ident in identifiers:
        unique_ident = base_ident
        suffix = 0
        while unique_ident in seen:
            suffix += 1
            unique_ident = f"{base_ident}_{suffix}"
        seen.add(unique_ident)
        deduped.append(unique_ident)

    return deduped


def _collect_check_identifiers_for_dataset(
    checks_paths: list[str],
    project_root: Path,
    dataset: str,
) -> list[str]:
    """Collect check identifiers for a dataset from all YAML files."""
    all_identifiers: list[str] = []
    seen: set[str] = set()

    for checks_path in checks_paths:
        yaml_path = Path(checks_path)
        if not yaml_path.is_absolute():
            yaml_path = project_root / yaml_path
        if not yaml_path.exists():
            continue

        identifiers = _parse_check_identifiers_from_yaml(yaml_path, dataset)
        for base_ident in identifiers:
            unique_ident = base_ident
            suffix = 0
            while unique_ident in seen:
                suffix += 1
                unique_ident = f"{base_ident}_{suffix}"
            seen.add(unique_ident)
            all_identifiers.append(unique_ident)

    return all_identifiers


def _filter_results_for_dataset(scan_results: Any, dataset: str) -> list[Any]:
    """Filter scan results to only include checks for the given dataset."""
    checks = getattr(scan_results, "checks", None) or getattr(scan_results, "check_results", [])
    if not isinstance(checks, (list, tuple)):
        return []

    filtered: list[Any] = []
    for check in checks:
        table = getattr(check, "table", None) or getattr(check, "table_name", None)
        dataset_attr = getattr(check, "dataset", None) or getattr(check, "dataset_name", None)
        check_dataset = table or dataset_attr
        if check_dataset and str(check_dataset) == dataset:
            filtered.append(check)

    return filtered


def _get_outcome(soda_check: Any) -> str:
    """Extract outcome (pass, warn, fail) from a Soda check result."""
    outcome = getattr(soda_check, "outcome", None) or getattr(soda_check, "result", "pass")
    return str(outcome).lower() if outcome else "pass"


def _get_check_name(soda_check: Any) -> str:
    """Extract check name from a Soda check result."""
    name = (
        getattr(soda_check, "name", None)
        or getattr(soda_check, "check_name", None)
        or getattr(soda_check, "identity", None)
    )
    return str(name) if name else "unknown"


def _get_severity(soda_check: Any) -> str:
    """Extract severity from a Soda check result."""
    severity = getattr(soda_check, "severity", None) or "warn"
    return str(severity).lower() if severity else "warn"


def _to_dagster_severity(severity: str) -> Any:
    """Convert Soda severity to Dagster AssetCheckSeverity."""
    from dagster import AssetCheckSeverity

    severity_lower = severity.lower() if severity else "warn"
    if severity_lower in ("error", "fail"):
        return AssetCheckSeverity.ERROR
    return AssetCheckSeverity.WARN


def _build_soda_result_map(
    dataset_results: list[Any], context: AssetCheckExecutionContext
) -> dict[str, Any]:
    """Build a map from Dagster-style check name (sanitized) to Soda check result.

    Matches on soda_check.name / check_name / identity and optionally definition.
    Logs a warning when a key collision occurs (duplicate key overwritten).
    """
    result_map: dict[str, Any] = {}
    for soda_check in dataset_results:
        name_key = _sanitize_check_name(_get_check_name(soda_check))
        if name_key and name_key != "check":
            if name_key in result_map:
                context.log.warning(
                    "Duplicate key collision in Soda result map for key: %s", name_key
                )
            result_map[name_key] = soda_check
        definition = getattr(soda_check, "definition", None)
        if definition:
            def_key = _sanitize_check_name(str(definition))
            if def_key and def_key != "check":
                if def_key in result_map:
                    context.log.warning(
                        "Duplicate key collision in Soda result map for key: %s", def_key
                    )
                result_map[def_key] = soda_check
    return result_map


@scaffold_with(SodaScanComponentScaffolder)
class SodaScanComponent(Component, Model, Resolvable):
    """A Dagster component that runs Soda Core scans and maps SodaCL check results to Dagster asset checks."""

    checks_paths: list[str] = Field(description="List of paths to SodaCL YAML check files.")
    configuration_path: str = Field(description="Path to the Soda configuration.yml file.")
    data_source_name: str = Field(
        description="The name of the data source connection defined in the configuration."
    )
    asset_key_map: Optional[dict[str, str]] = Field(
        default_factory=dict, description="Mapping of Soda dataset names to Dagster AssetKeys."
    )
    default_severity: str = Field(
        default="warn", description="Default severity level (e.g., warn, error) if not specified."
    )

    def _parse_datasets_from_yaml(self, yaml_path: Path) -> list[str]:
        """Extract dataset names from a SodaCL YAML file."""
        datasets: list[str] = []
        content = yaml_path.read_text()
        parsed = yaml.safe_load(content) or {}

        for key in parsed.keys():
            if isinstance(key, str) and key.startswith(SODACL_CHECKS_FOR_PREFIX):
                dataset_name = key[len(SODACL_CHECKS_FOR_PREFIX) :].strip()
                if dataset_name:
                    datasets.append(dataset_name)

        return datasets

    def _resolve_asset_key(self, soda_dataset: str) -> AssetKey:
        """Map Soda dataset name to Dagster AssetKey using asset_key_map."""
        asset_key_map = self.asset_key_map or {}
        if soda_dataset in asset_key_map:
            return AssetKey.from_user_string(asset_key_map[soda_dataset])
        return AssetKey.from_user_string(soda_dataset)

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        project_root = context.project_root
        asset_key_map = self.asset_key_map or {}
        check_defs: list[AssetChecksDefinition] = []
        seen_datasets: set[str] = set()

        for checks_path in self.checks_paths:
            yaml_path = Path(checks_path)
            if not yaml_path.is_absolute():
                yaml_path = project_root / yaml_path

            if not yaml_path.exists():
                continue

            datasets = self._parse_datasets_from_yaml(yaml_path)

            for soda_dataset in datasets:
                if soda_dataset in seen_datasets:
                    continue
                seen_datasets.add(soda_dataset)

                # Only produce checks for datasets in asset_key_map (or all if map is empty)
                if asset_key_map and soda_dataset not in asset_key_map:
                    continue

                check_identifiers = _collect_check_identifiers_for_dataset(
                    self.checks_paths,
                    project_root,
                    soda_dataset,
                )
                if not check_identifiers:
                    continue

                def _create_multi_check(
                    dataset: str,
                    proj_root: Path,
                    spec_names: list[str],
                ) -> AssetChecksDefinition:
                    asset_key = self._resolve_asset_key(dataset)
                    specs = [AssetCheckSpec(name=name, asset=asset_key) for name in spec_names]

                    @multi_asset_check(
                        specs=specs,
                        name=f"soda_scan_{dataset.replace('.', '_')}",
                        description=f"SodaCL checks for dataset {dataset}",
                    )
                    def _multi_check(
                        context: AssetCheckExecutionContext,
                    ) -> Iterator[AssetCheckResult]:
                        def _yield_failed_all(message: str) -> Iterator[AssetCheckResult]:
                            for check_name in spec_names:
                                yield AssetCheckResult(
                                    passed=False,
                                    asset_key=asset_key,
                                    check_name=check_name,
                                    metadata={
                                        "error": MetadataValue.text(message),
                                    },
                                )

                        try:
                            config_path = Path(self.configuration_path)
                            if not config_path.is_absolute():
                                config_path = proj_root / config_path

                            resolved_checks_paths: list[Path] = []
                            for cp in self.checks_paths:
                                p = Path(cp)
                                if not p.is_absolute():
                                    p = proj_root / p
                                if p.exists():
                                    resolved_checks_paths.append(p)

                            scan = Scan()
                            scan.set_data_source_name(self.data_source_name)
                            _add_configuration(scan, str(config_path))

                            for checks_file in resolved_checks_paths:
                                _add_sodacl_file(scan, str(checks_file))

                            scan.execute()

                            if hasattr(scan, "get_scan_results"):
                                scan_results = scan.get_scan_results()
                            elif hasattr(scan, "build_scan_results"):
                                scan_results = scan.build_scan_results()
                            else:
                                scan_results = scan
                            dataset_results = _filter_results_for_dataset(scan_results, dataset)
                        except Exception as e:
                            yield from _yield_failed_all(
                                f"Soda scan failed: {type(e).__name__}: {e}"
                            )
                            return

                        result_map = _build_soda_result_map(dataset_results, context)

                        for check_name in spec_names:
                            soda_check = result_map.get(check_name)
                            if soda_check is None:
                                context.log.warning(
                                    "No matching Soda result for check '%s'; yielding failed result.",
                                    check_name,
                                )
                                yield AssetCheckResult(
                                    passed=False,
                                    asset_key=asset_key,
                                    check_name=check_name,
                                    metadata={
                                        "error": MetadataValue.text(
                                            f"No matching Soda result for check '{check_name}'"
                                        ),
                                    },
                                )
                                continue

                            outcome = _get_outcome(soda_check)
                            severity = _get_severity(soda_check)
                            passed = outcome != "fail"

                            metadata: dict[str, Any] = {
                                "soda_outcome": outcome,
                                "severity": severity,
                            }
                            soda_check_name = _get_check_name(soda_check)
                            if soda_check_name != "unknown":
                                metadata["soda_check_name"] = soda_check_name
                            else:
                                context.log.warning(
                                    "Check name resolved to unknown for spec '%s'",
                                    check_name,
                                )
                            if hasattr(soda_check, "definition") and soda_check.definition:
                                metadata["check_definition"] = str(soda_check.definition)

                            yield AssetCheckResult(
                                passed=passed,
                                asset_key=asset_key,
                                check_name=check_name,
                                severity=_to_dagster_severity(severity),
                                metadata={
                                    k: MetadataValue.text(str(v)) for k, v in metadata.items()
                                },
                            )

                    return _multi_check

                check_defs.append(
                    _create_multi_check(
                        soda_dataset,
                        project_root,
                        check_identifiers,
                    )
                )

        return Definitions(asset_checks=check_defs)
