from typing import AbstractSet, NamedTuple, Optional


class AssetAndSLA(NamedTuple):
    key: str
    sla: Optional[str]
    """still need to nail down exactly what this means.  something like: a re-materialization should
    have completed by this tick since the last tick (which incorporates some root data that arrived
    since the last tick??)
    """

    deps: AbstractSet[str]
    processing_minutes: int  # how many minutes to allocate to materialize the asset


class ScheduledRun:
    keys: AbstractSet[str]
    minutes_from_start: int


EVERY_SIX_HOURS = "0 */6 * * *"

"""
Each test case defines the runs that we'd expect to be launched over the given span of minutes to
satisfy the given asset SLAs
"""
test_cases = [
    # One asset with an SLA
    dict(
        assets=[AssetAndSLA(sla="@hourly", key="a", deps=set(), processing_minutes=5)],
        span_minutes=60,
        runs=[ScheduledRun(keys={"a"}, minutes_from_start=60 - 5)],
    ),
    # A serial DAG with an SLA at the end
    dict(
        assets=[
            AssetAndSLA(sla=None, key="a", deps=[], processing_minutes=5),
            AssetAndSLA(sla="@hourly", key="b", deps={"a"}, processing_minutes=7),
        ],
        span_minutes=60,
        runs=[ScheduledRun(keys={"a", "b"}, minutes_from_start=60 - 12)],
    ),
    # A serial DAG where both assets have the same SLA
    dict(
        assets=[
            AssetAndSLA(sla="@hourly", key="a", deps=set(), processing_minutes=5),
            AssetAndSLA(sla="@hourly", key="b", deps={"a"}, processing_minutes=7),
        ],
        span_minutes=60,
        runs=[ScheduledRun(keys={"a", "b"}, minutes_from_start=60 - 12)],
    ),
    # A serial DAG where the first asset is every 6 hours and the second is daily
    dict(
        assets=[
            AssetAndSLA(sla="0 */6 * * *", key="a", deps=set(), processing_minutes=5),
            AssetAndSLA(sla="@daily", key="b", deps={"a"}, processing_minutes=7),
        ],
        span_minutes=24 * 60,
        runs=[
            ScheduledRun(keys={"a"}, minutes_from_start=6 * 60 - 5),
            ScheduledRun(keys={"a"}, minutes_from_start=12 * 60 - 5),
            ScheduledRun(keys={"a"}, minutes_from_start=18 * 60 - 5),
            ScheduledRun(keys={"a", "b"}, minutes_from_start=24 * 60 - 12),
        ],
    ),
    # A serial DAG where the first asset is daily and the second asset is every 6 hours (also pulls
    # from some data source that is constantly updating)
    dict(
        assets=[
            AssetAndSLA(sla="@daily", key="a", deps=set(), processing_minutes=5),
            AssetAndSLA(sla=EVERY_SIX_HOURS, key="b", deps={"a"}, processing_minutes=7),
        ],
        span_minutes=24 * 60,
        runs=[
            # should we update A as well? maybe memoization/versioning helps us decide?
            # if we want B to be as up-to-date as possible given other constraints, maybe yes?
            ScheduledRun(keys={"b"}, minutes_from_start=6 * 60 - 7),
            ScheduledRun(keys={"b"}, minutes_from_start=12 * 60 - 7),
            ScheduledRun(keys={"b"}, minutes_from_start=18 * 60 - 7),
            ScheduledRun(keys={"a", "b"}, minutes_from_start=24 * 60 - 12),
        ],
    ),
    # A serial DAG where the first asset has a 9 AM SLA and the second asset has a 10 AM SLA
    dict(
        assets=[
            AssetAndSLA(sla="0 9 * * *", key="a", deps=set(), processing_minutes=5),
            AssetAndSLA(sla="0 10 * * *", key="b", deps={"a"}, processing_minutes=7),
        ],
        span_minutes=24 * 60,
        # note: asset the 10 AM asset is expected to finish at 9:07
        runs=[ScheduledRun(keys={"a", "b"}, minutes_from_start=24 * 60 - 5)],
    ),
    # Two assets with the same SLA depend on the same asset without an SLA
    dict(
        assets=[
            AssetAndSLA(sla=None, key="a", deps=set(), processing_minutes=5),
            AssetAndSLA(sla="@hourly", key="b", deps={"a"}, processing_minutes=7),
            AssetAndSLA(sla="@hourly", key="c", deps={"a"}, processing_minutes=9),
        ],
        span_minutes=60,
        runs=[ScheduledRun(keys={"a", "b", "c"}, minutes_from_start=60 - (5 + 9))],
    ),
    # A daily asset and an every-six-hours asset depend on the same asset without an SLA
    dict(
        assets=[
            AssetAndSLA(sla=None, key="a", deps=set(), processing_minutes=5),
            AssetAndSLA(sla=EVERY_SIX_HOURS, key="b", deps={"a"}, processing_minutes=7),
            AssetAndSLA(sla="@daily", key="c", deps={"a"}, processing_minutes=9),
        ],
        span_minutes=24 * 60,
        runs=[
            ScheduledRun(keys={"a", "b"}, minutes_from_start=6 * 60 - 12),
            ScheduledRun(keys={"a", "b"}, minutes_from_start=12 * 60 - 12),
            ScheduledRun(keys={"a", "b"}, minutes_from_start=18 * 60 - 12),
            ScheduledRun(keys={"a", "b", "c"}, minutes_from_start=24 * 60 - 14),
        ],
    ),
    # A 9 AM asset and a 10 AM asset depend on the same asset without an SLA
    dict(
        assets=[
            AssetAndSLA(sla=None, key="a", deps=set(), processing_minutes=5),
            AssetAndSLA(sla="0 9 * * *", key="b", deps={"a"}, processing_minutes=7),
            AssetAndSLA(sla="0 10 * * *", key="c", deps={"a"}, processing_minutes=9),
        ],
        span_minutes=24 * 60,
        # note: the 10 AM asset is expected to finish at 9:02 AM
        runs=[ScheduledRun(keys={"a", "b", "c"}, minutes_from_start=9 * 60 - 12)],
    ),
]
