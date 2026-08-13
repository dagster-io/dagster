"""Debug-log parsing for dbt Cloud mid-run per-model monitoring.

dbt Cloud writes per-model progress lines to a step's ``debug_logs`` field as the
run streams — e.g. ``2 of 4 OK created sql table model dev.stg_customers ...``.
By polling ``debug_logs`` mid-run we can emit ``AssetMaterialization`` /
``AssetCheckResult`` / ``Output`` events for each model as it completes, rather
than waiting for the whole Cloud run to finish. Downstream ``AutomationCondition``
subscriptions react in seconds instead of minutes.

We prefer log parsing over ``run_results.json`` for this because ``run_results.json``
is only available after the whole run finishes — too late for mid-run reaction.

The regex intentionally accepts a wide set of dbt's progress verbiage (``created``,
``creating``, ``updated``, ``refreshing``, etc.) because dbt's exact wording depends
on adapter + materialization + version. We match the ``N of M STATUS ... name ..``
skeleton, which has been stable across recent dbt releases.
"""

import re
import time
from collections.abc import Iterator, Mapping
from enum import Enum
from typing import TYPE_CHECKING, Any

from dagster import (
    AssetCheckEvaluation,
    AssetCheckResult,
    AssetCheckSeverity,
    AssetExecutionContext,
    AssetMaterialization,
    Failure,
    MetadataValue,
    Output,
    get_dagster_logger,
)
from dagster._record import record

if TYPE_CHECKING:
    from dagster_dbt.cloud_v2.client import DbtCloudWorkspaceClient
    from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator

# Strip ANSI color codes (e.g. ``\x1b[32m``) — dbt Cloud debug logs come colorized.
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

# Model progress line. Example (Snowflake adapter):
#   1 of 4 OK created sql table model DEV.STG_CUSTOMERS .......... [SUCCESS 1 in 0.10s]
#   2 of 4 ERROR creating sql view model dev.stg_orders ........... [ERROR in 0.11s]
#   3 of 4 SKIP relation dev.stg_products ......................... [SKIP]
#
# We capture the terminal status word (OK / ERROR / SKIP) and the last dotted segment
# of the identifier (``STG_CUSTOMERS``, i.e. the model name). The prefix
# (``created`` / ``creating`` / etc.) is permissive on purpose.
_MODEL_LINE_RE = re.compile(
    r"\b(?P<current>\d+)\s+of\s+(?P<total>\d+)\s+"
    r"(?P<status>OK|ERROR|SKIP)\b"
    r".*?"
    r"(?:^|[\s.])(?P<qualified>[A-Za-z0-9_.]+?)"
    r"\s+\.{3,}",
    re.IGNORECASE,
)

# Test progress line. Example:
#   1 of 4 PASS not_null_customers_id ............................ [PASS in 0.10s]
#   2 of 4 FAIL not_null_orders_id ................................ [FAIL 1 in 0.11s]
#   3 of 4 WARN unique_customers_email ............................ [WARN 1 in 0.10s]
_TEST_LINE_RE = re.compile(
    r"\b(?P<current>\d+)\s+of\s+(?P<total>\d+)\s+"
    r"(?P<status>PASS|FAIL|WARN|ERROR)\s+"
    r"(?P<name>\S+)\s+\.{3,}",
    re.IGNORECASE,
)


class ParsedLogKind(str, Enum):
    """Kind of terminal event parsed out of a dbt Cloud step's debug log."""

    MODEL_OK = "MODEL_OK"
    MODEL_ERROR = "MODEL_ERROR"
    MODEL_SKIP = "MODEL_SKIP"
    TEST_PASS = "TEST_PASS"
    TEST_FAIL = "TEST_FAIL"
    TEST_WARN = "TEST_WARN"

    @property
    def is_failure(self) -> bool:
        """Failures include model errors and test failures (WARN is NOT a failure —
        matches dbt's own semantics where WARN is a soft signal, not a hard failure).
        """
        return self in (ParsedLogKind.MODEL_ERROR, ParsedLogKind.TEST_FAIL)


@record
class ParsedLogResult:
    """One terminal event parsed out of dbt Cloud debug logs.

    ``name`` is the model/test's short name (last dotted segment). Callers resolve
    it to a manifest ``unique_id`` via the current run's manifest — necessary
    because dbt logs schema-qualified names but Dagster keys off the unique_id.
    """

    kind: ParsedLogKind
    name: str


def strip_ansi(text: str) -> str:
    """Remove ANSI color codes so regex parsing doesn't fight terminal formatting."""
    return _ANSI_RE.sub("", text)


def _short_name(qualified: str) -> str:
    """Return the last dotted segment of a schema-qualified identifier.

    ``DEV.STG_CUSTOMERS`` -> ``STG_CUSTOMERS``; ``STG_ORDERS`` -> ``STG_ORDERS``.
    Case is preserved — dbt keys models by the source-file name which is
    case-sensitive on some adapters.
    """
    return qualified.rsplit(".", 1)[-1]


def parse_debug_logs(text: str) -> Iterator[ParsedLogResult]:
    """Yield one ``ParsedLogResult`` per matched progress line in ``text``.

    Order matches log order. Callers should dedupe by ``(kind_category, name)`` if
    they poll incrementally-growing logs (the same lines will appear on every poll).
    Deduping lives in the caller because a caller may hold cross-poll state that the
    parser shouldn't know about.
    """
    stripped = strip_ansi(text)
    for line in stripped.splitlines():
        model_match = _MODEL_LINE_RE.search(line)
        if model_match:
            status = model_match.group("status").upper()
            qualified = model_match.group("qualified")
            name = _short_name(qualified)
            if status == "OK":
                yield ParsedLogResult(kind=ParsedLogKind.MODEL_OK, name=name)
            elif status == "ERROR":
                yield ParsedLogResult(kind=ParsedLogKind.MODEL_ERROR, name=name)
            elif status == "SKIP":
                yield ParsedLogResult(kind=ParsedLogKind.MODEL_SKIP, name=name)
            continue

        test_match = _TEST_LINE_RE.search(line)
        if test_match:
            status = test_match.group("status").upper()
            name = test_match.group("name")
            if status == "PASS":
                yield ParsedLogResult(kind=ParsedLogKind.TEST_PASS, name=name)
            elif status in ("FAIL", "ERROR"):
                yield ParsedLogResult(kind=ParsedLogKind.TEST_FAIL, name=name)
            elif status == "WARN":
                yield ParsedLogResult(kind=ParsedLogKind.TEST_WARN, name=name)


def collect_step_debug_logs(run_details: dict) -> str:
    """Extract the concatenated ``debug_logs`` from every ``run_step`` in a run.

    dbt Cloud returns ``run_steps`` as a list on the run detail response when
    ``include_related=["run_steps", "debug_logs"]`` is passed. Each step has its
    own ``debug_logs`` field that grows as the step runs. We concatenate across
    steps so a single ``parse_debug_logs`` call sees the whole run's progress.
    """
    parts: list[str] = []
    for step in run_details.get("run_steps") or []:
        step_logs = step.get("debug_logs")
        if step_logs:
            parts.append(step_logs)
    return "\n".join(parts)


logger = get_dagster_logger()


def find_model_unique_id_by_name(manifest: Mapping[str, Any], name: str) -> str | None:
    """Case-insensitive lookup: given a model's short name (as it appears in dbt logs),
    return the manifest ``unique_id`` (e.g. ``model.jaffle_shop.stg_customers``) or
    ``None`` if not found. Case-insensitive because Snowflake logs uppercase names
    but manifests store the source-file case.
    """
    target = name.lower()
    nodes = manifest.get("nodes") or {}
    for uid, node in nodes.items():
        if uid.startswith("model.") and (node.get("name") or "").lower() == target:
            return uid
    return None


def find_test_unique_id_by_name(manifest: Mapping[str, Any], name: str) -> str | None:
    """Case-insensitive lookup: given a test's short name (as in dbt logs),
    return the manifest ``unique_id`` (e.g. ``test.jaffle_shop.not_null_customers_id``).
    """
    target = name.lower()
    nodes = manifest.get("nodes") or {}
    for uid, node in nodes.items():
        if uid.startswith("test.") and (node.get("name") or "").lower() == target:
            return uid
    return None


def _events_for_parsed(
    parsed: ParsedLogResult,
    manifest: Mapping[str, Any],
    translator: "DagsterDbtTranslator",
    context: AssetExecutionContext | None,
    partition_key: str | None,
    run_url: str | None,
) -> Iterator:
    """Convert one parsed log result into Dagster events (Output/AssetMaterialization
    for model completions, AssetCheckResult/AssetCheckEvaluation for tests).

    Silently skips events we can't map to the manifest (e.g. model_error where no
    materialization event fits, or unknown model names — rare, but possible when
    the manifest is stale relative to the run).
    """
    from dagster_dbt.asset_utils import build_dbt_specs, get_asset_check_key_for_test

    has_asset_def: bool = bool(context and context.has_assets_def)

    def _base_metadata(unique_id: str) -> dict:
        m: dict = {
            "unique_id": unique_id,
            "dagster_dbt/monitored": MetadataValue.bool(True),
        }
        if run_url:
            m["run_url"] = MetadataValue.url(run_url)
        return m

    if parsed.kind == ParsedLogKind.MODEL_OK:
        unique_id = find_model_unique_id_by_name(manifest, parsed.name)
        if unique_id is None:
            logger.warning(f"monitor_runs: no manifest match for model {parsed.name!r}; skipping.")
            return
        select = ".".join(manifest["nodes"][unique_id]["fqn"])
        asset_specs, _ = build_dbt_specs(
            manifest=manifest,
            translator=translator,
            select=select,
            exclude="",
            selector="",
            io_manager_key=None,
            project=None,
        )
        if not asset_specs:
            return
        spec = asset_specs[0]
        metadata = _base_metadata(unique_id)
        if context and has_asset_def:
            yield Output(
                value=None,
                output_name=spec.key.to_python_identifier(),
                metadata=metadata,
            )
        else:
            yield AssetMaterialization(
                asset_key=spec.key,
                metadata=metadata,
                partition=partition_key,
            )
        return

    if parsed.kind in (ParsedLogKind.MODEL_ERROR, ParsedLogKind.MODEL_SKIP):
        # No materialization for errored / skipped models — they didn't produce data.
        # The failure itself is surfaced via `Failure` raised at the end of the loop.
        return

    # Test events -> AssetCheck events.
    if parsed.kind in (ParsedLogKind.TEST_PASS, ParsedLogKind.TEST_FAIL, ParsedLogKind.TEST_WARN):
        unique_id = find_test_unique_id_by_name(manifest, parsed.name)
        if unique_id is None:
            logger.warning(f"monitor_runs: no manifest match for test {parsed.name!r}; skipping.")
            return
        asset_check_key = get_asset_check_key_for_test(
            manifest=manifest,
            dagster_dbt_translator=translator,
            test_unique_id=unique_id,
            project=None,
        )
        if asset_check_key is None:
            return
        passed = parsed.kind == ParsedLogKind.TEST_PASS
        severity = (
            AssetCheckSeverity.WARN
            if parsed.kind == ParsedLogKind.TEST_WARN
            else AssetCheckSeverity.ERROR
        )
        metadata = _base_metadata(unique_id)
        if context and has_asset_def and asset_check_key in context.selected_asset_check_keys:
            yield AssetCheckResult(
                passed=passed,
                asset_key=asset_check_key.asset_key,
                check_name=asset_check_key.name,
                metadata=metadata,
                severity=severity,
            )
        elif not has_asset_def:
            yield AssetCheckEvaluation(
                passed=passed,
                asset_key=asset_check_key.asset_key,
                check_name=asset_check_key.name,
                metadata=metadata,
                severity=severity,
            )


def _dedup_key(parsed: ParsedLogResult) -> tuple[str, str]:
    """Key used to dedupe repeated parsings of the same log line across polls.

    Group MODEL_* under ``"model"`` and TEST_* under ``"test"`` so a MODEL_ERROR and
    a hypothetical MODEL_OK for the same name (which would indicate a dbt log bug)
    aren't both emitted — first-seen wins.
    """
    prefix = "model" if parsed.kind.name.startswith("MODEL") else "test"
    return (prefix, parsed.name.lower())


def monitor_run_iter(
    run_id: int,
    client: "DbtCloudWorkspaceClient",
    manifest: Mapping[str, Any],
    translator: "DagsterDbtTranslator",
    context: AssetExecutionContext | None,
    fail_fast: bool,
    poll_interval: int,
    run_url: str | None = None,
) -> Iterator:
    """Poll a dbt Cloud run's step debug logs and yield Dagster events as models
    complete — before the whole Cloud run finishes.

    Contract:

    - Polls at ``poll_interval`` seconds.
    - Deduplicates against a per-invocation seen set, so repeated log lines across
      polls don't emit duplicate materializations.
    - On ``fail_fast=True``: on first model_error or test_fail, cancel the Cloud run
      via the API and raise ``Failure`` after yielding partials.
    - On ``fail_fast=False``: log the failure, keep going, yield partials as they
      arrive, then raise ``Failure`` after the run's own terminal status.
    - Successful models are always materialized — even when the run ultimately
      fails — matching OOTB partial-result behavior.
    """
    from dagster_dbt.cloud_v2.types import DbtCloudJobRunStatusType, DbtCloudRun

    seen: set[tuple[str, str]] = set()
    saw_failure = False
    terminal = {
        DbtCloudJobRunStatusType.SUCCESS,
        DbtCloudJobRunStatusType.ERROR,
        DbtCloudJobRunStatusType.CANCELLED,
    }
    partition_key: str | None = (
        context.partition_key if context and context.has_partition_key else None
    )

    while True:
        run_details = client.get_run_details(
            run_id=run_id,
            include_related=["run_steps", "debug_logs"],
        )
        run = DbtCloudRun.from_run_details(run_details=run_details)
        debug_logs = collect_step_debug_logs(run_details)

        for parsed in parse_debug_logs(debug_logs):
            key = _dedup_key(parsed)
            if key in seen:
                continue
            seen.add(key)

            yield from _events_for_parsed(
                parsed=parsed,
                manifest=manifest,
                translator=translator,
                context=context,
                partition_key=partition_key,
                run_url=run.url,
            )

            if parsed.kind.is_failure:
                saw_failure = True
                if fail_fast:
                    logger.warning(
                        f"monitor_runs (fail_fast=True): cancelling run {run_id} "
                        f"due to failure in {parsed.name!r}"
                    )
                    try:
                        client.cancel_run(run_id)
                    except Exception as e:
                        logger.warning(f"cancel_run failed for {run_id}: {e}")
                    raise Failure(
                        description=(
                            f"dbt Cloud run {run_id} cancelled by monitor_runs "
                            f"after {parsed.name!r} {parsed.kind.name}."
                        ),
                        metadata={
                            "dbt_cloud_run_id": MetadataValue.int(run_id),
                            "failed_name": MetadataValue.text(parsed.name),
                            "failure_kind": MetadataValue.text(parsed.kind.name),
                        },
                    )

        if run.status in terminal:
            break
        time.sleep(poll_interval)

    if run.status != DbtCloudJobRunStatusType.SUCCESS or saw_failure:
        raise Failure(
            description=(
                f"dbt Cloud run {run_id} finished with status "
                f"{run.status.name if run.status else 'UNKNOWN'}."
            ),
            metadata={
                "dbt_cloud_run_id": MetadataValue.int(run_id),
                "dbt_cloud_status": MetadataValue.text(
                    run.status.name if run.status else "UNKNOWN"
                ),
                **({"run_url": MetadataValue.url(run.url)} if run.url else {}),
            },
        )
