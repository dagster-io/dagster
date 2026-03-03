"""Dataset discovery for Spark Declarative Pipelines via dry-run and optional fallbacks.

This module runs ``spark-pipelines dry-run`` to discover datasets, parses JSON or
structured text output, and supports discovery_mode fallbacks (e.g. source_only).
State types (DiscoveredDataset, SparkPipelineState) are frozen dataclasses with
whitelist_for_serdes for Dagster serialize_value/deserialize_value compatibility.
"""

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from dagster_shared import check
from dagster_shared.serdes import whitelist_for_serdes

DiscoveryMode = Literal["dry_run_only", "dry_run_with_fallback", "source_only"]


class SparkPipelinesDryRunError(Exception):
    """Raised when ``spark-pipelines dry-run`` or ``spark-pipelines run`` fails.

    Attributes:
        message: Error description.
        stderr: Captured stderr or combined stdout/stderr from the process.
        returncode: Process exit code (non-zero on failure).
    """

    def __init__(self, message: str, stderr: str | None = None, returncode: int | None = None):
        super().__init__(message)
        self.stderr = stderr
        self.returncode = returncode


@dataclass(frozen=True)
class DryRunDatasetNode:
    """A single dataset node as reported by spark-pipelines dry-run.

    Attributes:
        name: Dataset identifier.
        raw: Raw dict from CLI output (e.g. JSON object for this node).
    """

    name: str
    raw: dict[str, Any]


@dataclass(frozen=True)
class DryRunReport:
    """Structured report produced by spark-pipelines dry-run (JSON or parsed text).

    Attributes:
        datasets: List of dataset nodes from the report.
        raw: Optional raw JSON dict when parsed from JSON; None for text fallback.
    """

    datasets: list[DryRunDatasetNode]
    raw: dict[str, Any] | None = None


@whitelist_for_serdes
@dataclass(frozen=True)
class DiscoveredDataset:
    """A dataset discovered for a Spark Declarative Pipeline (from dry-run or source).

    Used in cached state and for building AssetSpecs. Compatible with Dagster
    serialize_value/deserialize_value when used inside SparkPipelineState.

    Attributes:
        name: Dataset name (used as asset key component).
        attributes: Arbitrary metadata (e.g. dataset_type, schema info).
    """

    name: str
    attributes: dict[str, Any]


@whitelist_for_serdes
@dataclass(frozen=True)
class SparkPipelineState:
    """Cached state for a Spark Declarative Pipeline (discovered datasets).

    Persisted via Dagster serialize_value/deserialize_value. Used by
    SparkDeclarativePipelineComponent.write_state_to_path and build_defs_from_state.

    Attributes:
        datasets: List of discovered datasets.
        pipeline_spec_path: Path to the pipeline spec file (relative or absolute).
    """

    datasets: list[DiscoveredDataset]
    pipeline_spec_path: str


def discover_datasets_via_dry_run(
    pipeline_spec_path: str | Path,
    working_dir: str | Path | None = None,
    extra_args: list[str] | None = None,
) -> str:
    """Run `spark-pipelines dry-run` and return raw stdout.

    Args:
        pipeline_spec_path: Path to the pipeline spec file.
        working_dir: Optional working directory for the subprocess.
        extra_args: Optional extra CLI arguments.

    Returns:
        Raw stdout from the command.

    Raises:
        SparkPipelinesDryRunError: If the command fails or times out.
    """
    path_str = str(pipeline_spec_path)
    cmd = ["spark-pipelines", "dry-run", path_str]
    if extra_args:
        cmd.extend(extra_args)

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
        cwd=working_dir,
        timeout=300,
    )

    if result.returncode != 0:
        raise SparkPipelinesDryRunError(
            f"spark-pipelines dry-run failed with return code {result.returncode}",
            stderr=result.stderr,
            returncode=result.returncode,
        )

    return result.stdout


def extract_report(stdout: str) -> DryRunReport | None:
    """Extract a DryRunReport from dry-run stdout (JSON or structured text).

    Tries JSON first (e.g. --output json), then a simple text fallback.

    Args:
        stdout: Raw stdout string from spark-pipelines dry-run.

    Returns:
        A DryRunReport if parsing succeeded, otherwise None.
    """
    report = _extract_report_json(stdout)
    if report is not None:
        return report
    return _extract_report_text(stdout)


def _extract_report_json(stdout: str) -> DryRunReport | None:
    """Try to parse a JSON object or array from stdout and map to DryRunReport."""
    stripped = stdout.strip()
    if not stripped:
        return None

    # Try to find a JSON object or array (allow surrounding text)
    for pattern in (
        r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}",
        r"\[\s*\{[^]]*\}\s*\]",
    ):
        match = re.search(pattern, stdout, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
                return _json_to_report(data)
            except (json.JSONDecodeError, TypeError):
                continue

    # Try parsing the whole output as JSON
    try:
        data = json.loads(stripped)
        return _json_to_report(data)
    except (json.JSONDecodeError, TypeError):
        pass

    return None


def _json_to_report(data: Any) -> DryRunReport | None:
    """Map a JSON structure to DryRunReport. Placeholder: adapt to real CLI output shape."""
    if isinstance(data, dict):
        # Common keys: "datasets", "nodes", "sources", etc.
        nodes = data.get("datasets") or data.get("nodes") or data.get("sources") or []
    elif isinstance(data, list):
        nodes = data
    else:
        return None

    if not isinstance(nodes, list):
        return None

    dataset_nodes: list[DryRunDatasetNode] = []
    for item in nodes:
        if isinstance(item, dict):
            name = item.get("name") or item.get("id") or item.get("dataset") or str(item)
            if isinstance(name, dict):
                name = name.get("name") or name.get("id") or str(name)
            dataset_nodes.append(DryRunDatasetNode(name=str(name), raw=item))
        elif isinstance(item, str):
            dataset_nodes.append(DryRunDatasetNode(name=item, raw={"name": item}))

    return DryRunReport(datasets=dataset_nodes, raw=data if isinstance(data, dict) else None)


def _extract_report_text(stdout: str) -> DryRunReport | None:
    """Fallback: parse structured text lines (e.g. 'dataset: name' or bullet list)."""
    datasets: list[DryRunDatasetNode] = []
    for raw_line in stdout.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        # Match "dataset: foo" or "- foo" or "  - foo"
        for pattern in (r"dataset:\s*(.+)", r"^[-*]\s*(.+)", r"^\d+\.\s*(.+)"):
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if name:
                    datasets.append(DryRunDatasetNode(name=name, raw={"name": name}))
                break

    if not datasets:
        return None
    return DryRunReport(datasets=datasets, raw=None)


def parse_dry_run_output_to_datasets(stdout: str) -> list[DiscoveredDataset]:
    """Parse dry-run stdout into a list of DiscoveredDataset.

    Uses extract_report for JSON and text fallback; maps each node to DiscoveredDataset.

    Args:
        stdout: Raw stdout string from spark-pipelines dry-run.

    Returns:
        List of DiscoveredDataset (empty if report could not be parsed).
    """
    report = extract_report(stdout)
    if report is None:
        return []

    return [
        DiscoveredDataset(name=node.name, attributes=dict(node.raw)) for node in report.datasets
    ]


def discover_datasets_fn(
    pipeline_spec_path: str | Path,
    discovery_mode: DiscoveryMode,
    working_dir: str | Path | None = None,
    source_only_datasets: list[DiscoveredDataset] | None = None,
) -> list[DiscoveredDataset]:
    """Discover datasets for a Spark Declarative Pipeline based on discovery_mode.

    - dry_run_only: Run spark-pipelines dry-run and parse output; raise if it fails.
    - dry_run_with_fallback: Same as above, but on failure or empty result use source_only.
    - source_only: Do not run dry-run; use source_only_datasets if provided, else [].

    Args:
        pipeline_spec_path: Path to the pipeline spec.
        discovery_mode: One of dry_run_only, dry_run_with_fallback, source_only.
        working_dir: Optional working directory for dry-run.
        source_only_datasets: Optional list used when mode is source_only or as fallback.

    Returns:
        List of DiscoveredDataset.
    """
    check.inst_param(discovery_mode, "discovery_mode", str)
    source_list = source_only_datasets or []

    if discovery_mode == "source_only":
        return list(source_list)

    try:
        raw = discover_datasets_via_dry_run(
            pipeline_spec_path,
            working_dir=working_dir,
        )
        datasets = parse_dry_run_output_to_datasets(raw)
    except SparkPipelinesDryRunError:
        if discovery_mode == "dry_run_only":
            raise
        return list(source_list)

    if discovery_mode == "dry_run_with_fallback" and not datasets:
        return list(source_list)

    return datasets
