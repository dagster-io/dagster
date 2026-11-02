"""Hillpointe: the Friday Entrata report batch, read from the hpwh warehouse.

Replicates the FridayReports.xlsx Power Query. For a UTC window it takes the
latest row per expected job from dev.entrata_report_api_log and reports each
job's status in batch order. Two more endpoints back the same page: the raw
API log, and the SQL Agent history of the RestoreRealpageDaily job from msdb.
The SQL credentials are the same ones the pipelines use, loaded from the .env
file next to workspace.yaml.
"""

import os
from datetime import datetime, timezone

from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import JSONResponse

# Batch order of the Friday report, as in the spreadsheet.
FRIDAY_JOBS = [
    "entrata_catalog_sync",
    "buildings_and_units_sync",
    "work_orders_sync",
    "leases_sync",
    "customers_sync",
    "leads_sync",
    "box_score_90d",
    "box_score_audit_week",
    "rentroll_single_date",
    "collection_status_single_date",
    "screening_results_summary_sync",
    "comparative_delinquency_custom",
    "delinquency_custom",
    "resident_aged_receivables_custom",
]

# Jobs that count as EMPTY when they succeed without pulling anything.
EMPTY_CHECK_JOBS = {"customers_sync", "leads_sync"}

_SQL = f"""
SELECT job_name, started_at, finished_at, success, duration_seconds, message
FROM dev.entrata_report_api_log
WHERE started_at >= ? AND started_at < ?
  AND job_name IN ({", ".join("?" for _ in FRIDAY_JOBS)})
ORDER BY started_at DESC
"""

# The newest rows of the raw log, oldest first. Capped so the page stays quick.
API_LOG_LIMIT = 500
_API_LOG_SQL = """
SELECT id, job_name, started_at, finished_at, success
FROM (
    SELECT TOP (?) id, job_name, started_at, finished_at, success
    FROM dev.entrata_report_api_log
    ORDER BY id DESC
) newest
ORDER BY id ASC
"""

# SQL Agent history of the nightly Realpage restore; step 0 is the whole job.
_REALPAGE_SQL = """
SELECT
    j.name AS JobName,
    msdb.dbo.agent_datetime(h.run_date, h.run_time) AS RunDateTime,
    CASE h.run_status
        WHEN 0 THEN 'Failed'
        WHEN 1 THEN 'Succeeded'
        WHEN 2 THEN 'Retry'
        WHEN 3 THEN 'Canceled'
        WHEN 4 THEN 'In Progress'
    END AS RunStatus
FROM msdb.dbo.sysjobhistory h
INNER JOIN msdb.dbo.sysjobs j ON h.job_id = j.job_id
WHERE j.name = 'RestoreRealpageDaily' AND h.step_id = 0
ORDER BY h.run_date DESC, h.run_time DESC
"""

_ENV_VARS = ("SQL_SERVER_HOST", "SQL_USERNAME", "SQL_PASSWORD")


def _query(database: str, sql: str, *params) -> list[tuple]:
    # pyodbc is only installed on the VM; importing it here keeps the webserver
    # starting anywhere else.
    import pyodbc

    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={os.environ['SQL_SERVER_HOST']},{os.environ.get('SQL_SERVER_PORT', '1433')};"
        f"DATABASE={database};"
        f"UID={os.environ['SQL_USERNAME']};PWD={os.environ['SQL_PASSWORD']};"
        "Encrypt=yes;TrustServerCertificate=no;",
        timeout=15,
    )
    try:
        return conn.cursor().execute(sql, *params).fetchall()
    finally:
        conn.close()


def _fetch_rows(start: datetime, end: datetime) -> list[tuple]:
    return _query("hpwh", _SQL, start, end, *FRIDAY_JOBS)


def _status(job: str, row) -> str:
    if row is None:
        return "MISSING"
    _, _, finished_at, success, _, message = row
    if finished_at is None:
        return "RUNNING"
    if not success:
        return "FAILED"
    if job in EMPTY_CHECK_JOBS and message and ("rows=0" in message or "api_calls=0" in message):
        return "EMPTY"
    return "OK"


def _iso(value) -> str | None:
    # The table stores naive UTC datetimes.
    return value.replace(tzinfo=timezone.utc).isoformat() if value else None


def build_report(rows: list[tuple]) -> list[dict]:
    """Latest row per job, in batch order, with the spreadsheet's status rules."""
    latest: dict[str, tuple] = {}
    for row in rows:  # newest first, so the first row seen per job wins
        latest.setdefault(row[0], row)

    report = []
    for step, job in enumerate(FRIDAY_JOBS, start=1):
        row = latest.get(job)
        started_at, finished_at, duration, message = (
            (row[1], row[2], row[4], row[5]) if row else (None, None, None, None)
        )
        if duration is None and started_at and finished_at:
            duration = (finished_at - started_at).total_seconds()
        report.append(
            {
                "step": step,
                "job": job,
                "status": _status(job, row),
                "startedAt": _iso(started_at),
                "finishedAt": _iso(finished_at),
                "durationSeconds": duration,
                "message": message,
            }
        )
    return report


def _parse_utc(value: str | None) -> datetime:
    if not value:
        raise ValueError("missing")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("not timezone-aware")
    return parsed.astimezone(timezone.utc).replace(tzinfo=None)


def _not_configured() -> JSONResponse | None:
    missing = [name for name in _ENV_VARS if not os.environ.get(name)]
    if not missing:
        return None
    return JSONResponse(
        {"error": f"SQL Server is not configured on this webserver: {', '.join(missing)} not set"},
        503,
    )


async def friday_report_endpoint(request: Request) -> JSONResponse:
    """GET /hillpointe/friday_report?start=<iso>&end=<iso>, both UTC instants."""
    try:
        start = _parse_utc(request.query_params.get("start"))
        end = _parse_utc(request.query_params.get("end"))
    except ValueError as exc:
        return JSONResponse({"error": f"start and end must be ISO-8601 instants ({exc})"}, 400)

    if error := _not_configured():
        return error

    try:
        rows = await run_in_threadpool(_fetch_rows, start, end)
    except Exception as exc:
        return JSONResponse({"error": f"Could not read the report log: {exc}"}, 502)

    return JSONResponse({"jobs": build_report(rows)})


async def entrata_api_log_endpoint(request: Request) -> JSONResponse:
    """GET /hillpointe/entrata_api_log: the newest rows of the raw log, oldest first."""
    if error := _not_configured():
        return error

    try:
        rows = await run_in_threadpool(_query, "hpwh", _API_LOG_SQL, API_LOG_LIMIT)
    except Exception as exc:
        return JSONResponse({"error": f"Could not read the report log: {exc}"}, 502)

    return JSONResponse(
        {
            "rows": [
                {
                    "id": row_id,
                    "job": job,
                    "startedAt": _iso(started_at),
                    "finishedAt": _iso(finished_at),
                    "success": None if success is None else bool(success),
                }
                for row_id, job, started_at, finished_at, success in rows
            ]
        }
    )


async def realpage_restore_endpoint(request: Request) -> JSONResponse:
    """GET /hillpointe/realpage_restore: SQL Agent history of RestoreRealpageDaily."""
    if error := _not_configured():
        return error

    try:
        rows = await run_in_threadpool(_query, "msdb", _REALPAGE_SQL)
    except Exception as exc:
        return JSONResponse({"error": f"Could not read the SQL Agent history: {exc}"}, 502)

    # agent_datetime is the SQL Server's local clock, so it is passed through as-is.
    return JSONResponse(
        {
            "rows": [
                {"job": job, "runAt": run_at.isoformat() if run_at else None, "status": status}
                for job, run_at, status in rows
            ]
        }
    )
