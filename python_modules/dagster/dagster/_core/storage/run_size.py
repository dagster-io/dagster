"""Measures how large a run is once serialized, for deployments that cap run size.

Run storage enforces the cap when a run is added; the sensor daemon uses the same measurement
to decide whether a run request is worth persisting on a tick.
"""

from dagster._core.definitions.run_request import RunRequest
from dagster._core.storage.dagster_run import DagsterRun
from dagster._record import copy
from dagster._serdes import serialize_value


def get_run_size_bytes(dagster_run: DagsterRun) -> int:
    """Serialized size of a run, excluding fields the system populates.

    The cap targets user-controlled bloat (large run config or tags), so selections, step keys
    and partition subsets are cleared before measuring.
    """
    return len(
        serialize_value(
            copy(
                dagster_run,
                asset_selection=None,
                asset_check_selection=None,
                op_selection=None,
                resolved_op_selection=None,
                step_keys_to_execute=None,
                partitions_subset=None,
            )
        )
    )


def estimate_run_size_bytes(run_request: RunRequest) -> int:
    """Size of the run a request would create, measured as `get_run_size_bytes` would measure it.

    An underestimate: the launched run also carries the job's run tags and the sensor/tick tags.
    """
    return get_run_size_bytes(
        DagsterRun(
            job_name=run_request.job_name or "",
            run_config=run_request.run_config,
            tags=run_request.tags,
        )
    )


def exceeds_run_size_limit(run_request: RunRequest, limit: int) -> bool:
    """Whether the run a request would create is large enough for run storage to reject it.

    Since the estimate is conservative, a request that passes here may still be rejected at
    launch; the point is to catch the requests that are oversized by a wide margin.
    """
    return estimate_run_size_bytes(run_request) >= limit
