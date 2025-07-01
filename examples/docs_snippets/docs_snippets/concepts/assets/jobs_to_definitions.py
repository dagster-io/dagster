# start_marker_job
import dagster as dg


@dg.asset
def number_asset():
    yield dg.MaterializeResult(
        metadata={
            "number": 1,
        }
    )


# end_marker_job


# start_marker_job_definition
import dagster as dg


@dg.job
def number_asset_job():
    number_asset()


# end_marker_job_definition
