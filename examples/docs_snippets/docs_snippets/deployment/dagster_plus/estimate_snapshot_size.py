from dagster import Definitions, asset, serialize_value
from dagster._core.remote_representation.external_data import RepositorySnap
from dagster._core.snap.job_snapshot import JobSnap


# Replace these example assets with your own Definitions object.
@asset
def upstream() -> None: ...


@asset(deps=[upstream])
def downstream() -> None: ...


defs = Definitions(assets=[upstream, downstream])


def _mb(serialized: str) -> float:
    return len(serialized.encode("utf-8")) / 1024 / 1024


repo_def = defs.get_repository_def()

# Repository snapshot. defer_snapshots=True matches how Dagster+ stores it: job
# snapshots are persisted separately, so the repository snapshot holds job
# references rather than full job data.
repo_snap = RepositorySnap.from_def(repo_def, defer_snapshots=True)
print(f"Repository snapshot: {_mb(serialize_value(repo_snap)):.2f} MB")  # noqa: T201

# Each job snapshot. get_all_jobs() includes the built-in asset job
# ("__ASSET_JOB") that Dagster runs when no named job is specified.
for job_def in sorted(repo_def.get_all_jobs(), key=lambda j: j.name):
    job_snap = JobSnap.from_job_def(job_def)
    print(f"Job '{job_def.name}' snapshot: {_mb(serialize_value(job_snap)):.2f} MB")  # noqa: T201
