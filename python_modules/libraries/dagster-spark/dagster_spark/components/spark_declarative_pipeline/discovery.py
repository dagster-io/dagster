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

from dagster import get_dagster_logger
from dagster_shared import check  # type: ignore[reportMissingImports]
from dagster_shared.serdes import whitelist_for_serdes  # type: ignore[reportMissingImports]

# Guardrail to prevent daemon hangs.
DRY_RUN_TIMEOUT_SECONDS = 60

DiscoveryMode = Literal["dry_run_only", "dry_run_with_fallback", "source_only"]


class SparkPipelinesError(Exception):
    """Base exception for Spark Declarative Pipeline operations (dry-run and execution)."""


class SparkPipelinesDryRunError(SparkPipelinesError):
    """Raised when ``spark-pipelines dry-run`` fails.

    Attributes:
        message: Error description.
        stderr: Captured stderr or combined stdout/stderr from the process.
        returncode: Process exit code (non-zero on failure).
    """

    def __init__(self, message: str, stderr: str | None = None, returncode: int | None = None):
        super().__init__(message)
        self.stderr = stderr
        self.returncode = returncode


class SparkPipelinesExecutionError(SparkPipelinesError):
    """Raised when ``spark-pipelines run`` fails.

    Attributes:
        message: Error description.
        stderr: Captured stderr or combined stdout/stderr from the process.
        returncode: Process exit code (non-zero on failure).
    """

    def __init__(self, message: str, stderr: str | None = None, returncode: int | None = None):
        super().__init__(message)
        self.stderr = stderr
        self.returncode = returncode


class DuplicateDatasetNamesError(ValueError):
    """Raised when discovered datasets contain duplicate names after normalization.

    Attributes:
        duplicate_names: List of dataset names that appear more than once.
    """

    def __init__(self, message: str, duplicate_names: list[str]):
        super().__init__(message)
        self.duplicate_names = duplicate_names


@dataclass(frozen=True)
class DryRunDatasetNode:
    """A single dataset node as reported by spark-pipelines dry-run.

    Attributes:
        name: Dataset identifier.
        raw: Raw dict from CLI output (e.g. JSON object for this node).
        inferred_deps: Upstream dataset names extracted from the node (e.g. deps, dependencies).
    """

    name: str
    raw: dict[str, Any]
    inferred_deps: tuple[str, ...] = ()


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
        dataset_type: Type of dataset (e.g. table, materialized_view, temporary_view).
        source_file: Path to source file where dataset was defined, if known.
        source_line: Line number in source file, if known.
        inferred_deps: Upstream dataset names (e.g. catalog.schema.table).
        discovery_method: How the dataset was discovered (e.g. dry_run, source_fallback).
    """

    name: str
    dataset_type: str
    source_file: str | None
    source_line: int | None
    inferred_deps: list[str]
    discovery_method: str


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
    spark_pipelines_cmd: str = "spark-pipelines",
) -> str:
    """Run `spark-pipelines dry-run` and return raw stdout.

    Args:
        pipeline_spec_path: Path to the pipeline spec file.
        working_dir: Optional working directory for the subprocess.
        extra_args: Optional extra CLI arguments.
        spark_pipelines_cmd: Executable name or path for the spark-pipelines CLI.

    Returns:
        Raw stdout from the command.

    Raises:
        SparkPipelinesDryRunError: If the command fails or times out.
    """
    path_str = str(pipeline_spec_path)
    cmd = [spark_pipelines_cmd, "dry-run", "--spec", path_str]
    if extra_args:
        cmd.extend(extra_args)

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
        cwd=working_dir,
        timeout=DRY_RUN_TIMEOUT_SECONDS,
    )

    if result.returncode != 0:
        raise SparkPipelinesDryRunError(
            f"{spark_pipelines_cmd} dry-run failed with return code {result.returncode}",
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


# Optional log-level prefix before JSON in stdout (e.g. "INFO: " or "WARN: ")
_LOG_PREFIX = re.compile(r"^\s*(?:\[?\w+\]?:\s*)?", re.IGNORECASE)


def _extract_report_json(stdout: str) -> DryRunReport | None:
    """Try to parse a JSON object or array from stdout and map to DryRunReport.

    Iterates through lines and tries json.loads on stripped content (with optional
    log-style prefix stripped) to avoid capturing arbitrary log text between
    first '{' and last '}' which can crash json.loads.
    """
    stripped = stdout.strip()
    if not stripped:
        return None

    # Try parsing the whole output as JSON first
    try:
        data = json.loads(stripped)
        report = _json_to_report(data)
        if report is not None:
            return report
    except (json.JSONDecodeError, TypeError):
        pass

    # Line-by-line: try each line (and optional log prefix strip) to find valid JSON
    for raw_line in stdout.splitlines():
        line = raw_line.strip()
        if not line or ("{" not in line and "[" not in line):
            continue
        for candidate in (line, _LOG_PREFIX.sub("", line)):
            if not candidate:
                continue
            try:
                data = json.loads(candidate)
                report = _json_to_report(data)
                if report is not None:
                    return report
            except (json.JSONDecodeError, TypeError):
                pass
        # Single line may have leading/trailing text; try substring from first { or [
        for start_char, end_char in (("{", "}"), ("[", "]")):
            i = line.find(start_char)
            if i == -1:
                continue
            j = line.rfind(end_char)
            if j != -1 and j > i:
                try:
                    data = json.loads(line[i : j + 1])
                    report = _json_to_report(data)
                    if report is not None:
                        return report
                except (json.JSONDecodeError, TypeError):
                    pass

    return None


def _extract_deps_from_node(item: dict[str, Any]) -> tuple[str, ...]:
    """Extract upstream dataset names from a JSON node (deps, dependencies, upstream_dataset_names)."""
    deps = item.get("upstream_dataset_names") or item.get("dependencies") or item.get("deps") or []
    if isinstance(deps, str):
        deps = [deps]
    if not isinstance(deps, list):
        return ()
    return tuple(str(d) for d in deps if isinstance(d, str))


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
            inferred_deps = _extract_deps_from_node(item)
            dataset_nodes.append(
                DryRunDatasetNode(name=str(name), raw=item, inferred_deps=inferred_deps)
            )
        elif isinstance(item, str):
            dataset_nodes.append(DryRunDatasetNode(name=item, raw={"name": item}, inferred_deps=()))

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
                    datasets.append(
                        DryRunDatasetNode(name=name, raw={"name": name}, inferred_deps=())
                    )
                break

    if not datasets:
        return None
    return DryRunReport(datasets=datasets, raw=None)


# Regex for source-only discovery: Python decorator (optional dp. prefix, optional args) + function name
_PY_DATASET_DECORATOR = re.compile(
    r"@(?:dp\.)?(materialized_view|table|streaming_table|temporary_view)(?:\([^)]*\))?\s*\n\s*def\s+(\w+)\s*\(",
    re.MULTILINE,
)
# Regex for source-only discovery: SQL CREATE statement (capture type and catalog.schema.table)
_SQL_CREATE_DATASET = re.compile(
    r"CREATE\s+(MATERIALIZED\s+VIEW|STREAMING\s+TABLE|TABLE|VIEW)\s+(?:IF\s+NOT\s+EXISTS\s+)?([\w.]+)",
    re.IGNORECASE,
)


def discover_datasets_from_sources(pipeline_spec_path: Path) -> list[DiscoveredDataset]:
    """Discover datasets by scanning source files under the pipeline spec directory.

    Best-effort fallback only: scans the directory (and subdirectories) of
    pipeline_spec_path for .py and .sql files using regex. Does not evaluate
    dynamic Python arguments (e.g. @dp.table(name="tbl")) or resolve complex
    imports (e.g. @table). Prefer dry-run discovery when available.

    For Python: matches @(dp.)?(materialized_view|table|streaming_table|temporary_view)
    with optional parentheses and arguments, then def my_dataset_name(.
    For SQL: CREATE (MATERIALIZED VIEW|...) [IF NOT EXISTS] my_dataset_name.

    Args:
        pipeline_spec_path: Path to the pipeline spec file (its parent is scanned).

    Returns:
        List of DiscoveredDataset (deduplicated by name). Returns [] on any failure.
    """
    logger = get_dagster_logger()
    try:
        root = Path(pipeline_spec_path).resolve()
        if root.is_file():
            root = root.parent
    except Exception as e:
        logger.warning(
            "Failed to resolve pipeline spec path %s: %s",
            pipeline_spec_path,
            e,
            exc_info=True,
        )
        return []

    if not root.exists():
        logger.warning("Pipeline spec directory does not exist: %s", root)
        return []

    seen: set[str] = set()
    result: list[DiscoveredDataset] = []
    scanned_files = 0

    try:
        for ext in ("*.py", "*.sql"):
            for path in root.rglob(ext):
                try:
                    text = path.read_text(encoding="utf-8", errors="replace")
                    scanned_files += 1
                except Exception as e:
                    logger.warning(
                        "Failed to read source file %s: %s",
                        path,
                        e,
                        exc_info=True,
                    )
                    continue
                if ext == "*.py":
                    for m in _PY_DATASET_DECORATOR.finditer(text):
                        name = m.group(2)
                        if name not in seen:
                            seen.add(name)
                            result.append(
                                DiscoveredDataset(
                                    name=name,
                                    dataset_type=m.group(1),
                                    source_file=str(path),
                                    source_line=None,
                                    inferred_deps=[],
                                    discovery_method="source_fallback",
                                )
                            )
                else:
                    for m in _SQL_CREATE_DATASET.finditer(text):
                        raw_type = m.group(1)
                        dataset_type_sql = raw_type.lower().replace(" ", "_")
                        name = m.group(2)
                        if name not in seen:
                            seen.add(name)
                            result.append(
                                DiscoveredDataset(
                                    name=name,
                                    dataset_type=dataset_type_sql,
                                    source_file=str(path),
                                    source_line=None,
                                    inferred_deps=[],
                                    discovery_method="source_fallback",
                                )
                            )
    except Exception as e:
        logger.warning(
            "Failed to discover datasets from sources under %s: %s",
            root,
            e,
            exc_info=True,
        )
        return []

    logger.info(
        "Scanned %d files for static dataset discovery, found %d datasets.",
        scanned_files,
        len(result),
    )
    return result


def _node_dataset_type(raw: dict[str, Any]) -> str:
    """Extract dataset_type from a raw node (type, dataset_type, or default 'table')."""
    t = raw.get("type") or raw.get("dataset_type")
    if isinstance(t, str):
        return t.lower().replace(" ", "_")
    return "table"


def parse_dry_run_output_to_datasets(stdout: str) -> list[DiscoveredDataset]:
    """Parse dry-run stdout into a list of DiscoveredDataset.

    Uses extract_report for JSON and text fallback; maps each node to DiscoveredDataset
    with explicit dataset_type, source_file, source_line, inferred_deps, discovery_method.

    Args:
        stdout: Raw stdout string from spark-pipelines dry-run.

    Returns:
        List of DiscoveredDataset (empty if report could not be parsed).
    """
    report = extract_report(stdout)
    if report is None:
        return []

    result: list[DiscoveredDataset] = []
    for node in report.datasets:
        raw = node.raw
        source_file = raw.get("source_file") or raw.get("source")
        if isinstance(source_file, str):
            pass
        else:
            source_file = None
        source_line = raw.get("source_line")
        if isinstance(source_line, int):
            pass
        else:
            source_line = None
        result.append(
            DiscoveredDataset(
                name=node.name,
                dataset_type=_node_dataset_type(raw),
                source_file=source_file,
                source_line=source_line,
                inferred_deps=list(node.inferred_deps),
                discovery_method="dry_run",
            )
        )
    return result


def _validate_no_duplicate_dataset_names(datasets: list[DiscoveredDataset]) -> None:
    """Raise DuplicateDatasetNamesError if any dataset names are duplicated after normalization.

    Normalization: strip and lowercased name for comparison.
    """
    from collections import Counter

    normalized = [ds.name.strip().lower() for ds in datasets]
    counts = Counter(normalized)
    duplicate_normalized = [k for k, c in counts.items() if c > 1]
    if not duplicate_normalized:
        return
    # Report original names for duplicated normalized keys (first occurrence each)
    seen_orig: dict[str, str] = {}
    for ds in datasets:
        key = ds.name.strip().lower()
        if key not in seen_orig:
            seen_orig[key] = ds.name
    duplicate_names = [seen_orig[k] for k in duplicate_normalized]
    raise DuplicateDatasetNamesError(
        f"Duplicate dataset names after normalization: {duplicate_names}",
        duplicate_names=duplicate_names,
    )


def discover_datasets_fn(
    pipeline_spec_path: str | Path,
    discovery_mode: DiscoveryMode,
    working_dir: str | Path | None = None,
    source_only_datasets: list[DiscoveredDataset] | None = None,
    spark_pipelines_cmd: str = "spark-pipelines",
    dry_run_extra_args: list[str] | None = None,
) -> list[DiscoveredDataset]:
    """Discover datasets for a Spark Declarative Pipeline based on discovery_mode.

    - dry_run_only: Run spark-pipelines dry-run and parse output; raise if it fails.
    - dry_run_with_fallback: Same as above, but on failure or empty result use source_only.
    - source_only: Do not run dry-run; use source_only_datasets if provided, else discover from sources.

    Duplicate dataset names (after normalization: strip + lowercase) are a hard error.

    Args:
        pipeline_spec_path: Path to the pipeline spec.
        discovery_mode: One of dry_run_only, dry_run_with_fallback, source_only.
        working_dir: Optional working directory for dry-run.
        source_only_datasets: Optional list used when mode is source_only or as fallback.
        spark_pipelines_cmd: Executable name or path for the spark-pipelines CLI.
        dry_run_extra_args: Optional extra CLI arguments for dry-run.

    Returns:
        List of DiscoveredDataset.

    Raises:
        DuplicateDatasetNamesError: If the discovered list contains duplicate names.
    """
    check.inst_param(discovery_mode, "discovery_mode", str)
    source_list = source_only_datasets
    extra_args = dry_run_extra_args or []

    def _return(datasets: list[DiscoveredDataset]) -> list[DiscoveredDataset]:
        _validate_no_duplicate_dataset_names(datasets)
        return list(datasets)

    if discovery_mode == "source_only":
        if source_list is not None:
            return _return(source_list)
        return _return(discover_datasets_from_sources(Path(pipeline_spec_path)))

    try:
        raw = discover_datasets_via_dry_run(
            pipeline_spec_path,
            working_dir=working_dir,
            extra_args=extra_args,
            spark_pipelines_cmd=spark_pipelines_cmd,
        )
        datasets = parse_dry_run_output_to_datasets(raw)
    except SparkPipelinesDryRunError:
        if discovery_mode == "dry_run_only":
            raise
        if source_list is not None:
            return _return(source_list)
        return _return(discover_datasets_from_sources(Path(pipeline_spec_path)))

    if discovery_mode == "dry_run_with_fallback" and not datasets:
        if source_list is not None:
            return _return(source_list)
        return _return(discover_datasets_from_sources(Path(pipeline_spec_path)))

    return _return(datasets)
