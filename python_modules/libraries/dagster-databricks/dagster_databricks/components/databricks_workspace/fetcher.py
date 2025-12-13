import asyncio
from typing import Any, Optional

import aiohttp
from dagster import get_dagster_logger

from dagster_databricks.components.databricks_asset_bundle.configs import DatabricksJob
from dagster_databricks.components.databricks_workspace.schema import DatabricksFilter

logger = get_dagster_logger()


async def _fetch_json(
    session: aiohttp.ClientSession, url: str, params: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    async with session.get(url, params=params) as resp:
        resp.raise_for_status()
        return await resp.json()


def _extract_host_and_token_from_client(workspace_client: Any) -> tuple[str, str]:
    # Try several common attribute paths used by the databricks SDK to locate host and token
    candidates = []

    # Direct attributes
    candidates.append(
        (getattr(workspace_client, "host", None), getattr(workspace_client, "token", None))
    )
    candidates.append(
        (getattr(workspace_client, "_host", None), getattr(workspace_client, "_token", None))
    )

    # Common container attributes
    for attr in ("config", "_config", "client", "_client", "api_client", "_api_client"):
        obj = getattr(workspace_client, attr, None)
        if obj is None:
            continue
        candidates.append((getattr(obj, "host", None), getattr(obj, "token", None)))
        candidates.append((getattr(obj, "_host", None), getattr(obj, "_token", None)))
        # nested config
        cfg = getattr(obj, "config", None)
        if cfg is not None:
            candidates.append((getattr(cfg, "host", None), getattr(cfg, "token", None)))
            candidates.append((getattr(cfg, "_host", None), getattr(cfg, "_token", None)))

    for host, token in candidates:
        if host and token:
            host_str = str(host)
            token_str = str(token)

            if not host_str.startswith("http"):
                host_str = "https://" + host_str.lstrip("/")
            return host_str.rstrip("/"), token_str

    raise ValueError(
        "Could not extract host and token from provided workspace_client. "
        "Pass a databricks.sdk WorkspaceClient or provide host/token accessors."
    )


async def fetch_databricks_workspace_data(
    workspace_client: Any, databricks_filter: DatabricksFilter
) -> list[Any]:
    """Fetch Databricks jobs and full job details asynchronously.

    Steps:
    - Extract host and token from `workspace_client`.
    - Call `/api/2.1/jobs/list` with pagination to retrieve all jobs.
    - Apply `databricks_filter.include_job` to raw jobs.
    - For each matching job, call `/api/2.1/jobs/get?job_id=...` in parallel.
    - Deserialize each full job JSON into `Job` if available, otherwise return raw dict.

    Raises:
        ValueError: If host/token cannot be found.
        aiohttp.ClientResponseError: If the API request fails.
    """
    host, token = _extract_host_and_token_from_client(workspace_client)

    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    # Use a client session; do not trust workspace_client's internals for async requests
    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
        # Step A: list jobs with pagination
        jobs_list: list[dict[str, Any]] = []
        next_page_token: Optional[str] = None
        list_url = f"{host}/api/2.1/jobs/list"

        while True:
            params: dict[str, Any] = {}
            if next_page_token:
                params["page_token"] = next_page_token
            else:
                params["limit"] = 1000

            resp_json = await _fetch_json(session, list_url, params=params)

            # Databricks 2.1 jobs.list returns 'jobs' and optionally 'next_page_token'
            page_jobs = resp_json.get("jobs") or []
            jobs_list.extend(page_jobs)

            next_page_token = resp_json.get("next_page_token")
            if not next_page_token:
                break

        filtered_jobs = [job for job in jobs_list if databricks_filter.include_job(job)]

        get_url = f"{host}/api/2.1/jobs/get"

        sem = asyncio.Semaphore(20)

        async def _fetch_full(job_info: dict[str, Any]) -> DatabricksJob:
            job_id = job_info.get("job_id") or job_info.get("jobId")
            if not job_id:
                raise ValueError(f"Job missing job_id: {job_info}")

            params = {"job_id": job_id}

            async with sem:
                full_json = await _fetch_json(session, get_url, params=params)

            settings = full_json.get("settings", {})
            job_name = settings.get("name", f"job_{job_id}")
            tasks = settings.get("tasks", [])

            return DatabricksJob(job_id=job_id, name=job_name, tasks=tasks)

        tasks = [_fetch_full(job) for job in filtered_jobs]
        results = await asyncio.gather(*tasks, return_exceptions=False)

    return results