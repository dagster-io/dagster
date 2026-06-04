"""Verify the dagster_essentials course runs end-to-end on lightweight dagster,
including the geopandas/matplotlib map + chart outputs.

Part A imports the REAL course modules (orchestration + viz assets) and confirms
they resolve under lightweight dagster + the dagster_duckdb shim.

Part B executes the REAL course assets against small local sample data (with
valid Manhattan WKT geometry) and writes every output into
`compact_tools/course_verification_output/`:
    data/raw/         sample inputs (taxi_zones.csv, taxi_trips_2023-01.parquet)
    data/staging/     manhattan_stats.geojson      (manhattan_stats asset)
    data/outputs/     trips_by_week.csv            (trips_by_week asset)
                      manhattan_map.png            (manhattan_map asset — THE MAP)
                      adhoc_manhattan.png          (adhoc_request asset — chart)
    course.duckdb     the DuckDB database

Only the network download in the taxi_*_file assets is skipped (needs internet);
everything downstream is the unmodified course asset code.
"""

import os
import shutil
import sys

COURSE_SRC = (
    "/Users/Gurdeep/consumeriq/project-dagster-university/"
    "dagster_university/dagster_essentials/src"
)
sys.path.insert(0, COURSE_SRC)

import duckdb  # noqa: E402

import dagster as dg  # noqa: E402

L9 = "dagster_essentials.completed.lesson_9.defs"

# small squares inside the Manhattan map bbox the course uses (lon/lat WKT)
ZONE_A_WKT = "POLYGON((-73.99 40.74, -73.97 40.74, -73.97 40.76, -73.99 40.76, -73.99 40.74))"
ZONE_B_WKT = "POLYGON((-73.96 40.77, -73.94 40.77, -73.94 40.79, -73.96 40.79, -73.96 40.77))"


def part_a_imports():
    import importlib

    mods = {
        m: importlib.import_module(f"{L9}.{m}")
        for m in ("resources", "partitions", "jobs", "schedules", "sensors")
    }
    trips = importlib.import_module(f"{L9}.assets.trips")
    metrics = importlib.import_module(f"{L9}.assets.metrics")
    requests_mod = importlib.import_module(f"{L9}.assets.requests")

    print("PART A — real course modules import + resolve under lightweight dagster")
    print(f"  jobs:      {[j.name for j in (mods['jobs'].trip_update_job, mods['jobs'].weekly_update_job, mods['jobs'].adhoc_request_job)]}")
    print(f"  schedules: {[mods['schedules'].trip_update_schedule.name, mods['schedules'].weekly_update_schedule.name]}")
    print(f"  sensor:    {mods['sensors'].adhoc_request_sensor.name}")
    print(f"  assets:    taxi_zones, taxi_trips, trips_by_week, "
          f"{metrics.manhattan_stats.key.to_user_string()}, manhattan_map, adhoc_request")
    return trips, metrics, requests_mod


def write_sample_inputs():
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/staging", exist_ok=True)
    os.makedirs("data/outputs", exist_ok=True)

    # zones CSV (columns match the course's taxi_zones query: LocationID, zone, borough, the_geom)
    import csv

    with open("data/raw/taxi_zones.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["LocationID", "zone", "borough", "the_geom"])
        w.writerow([1, "Midtown", "Manhattan", ZONE_A_WKT])
        w.writerow([2, "Harlem", "Manhattan", ZONE_B_WKT])

    # trips parquet via duckdb (avoids pyarrow); pickups in the first week of Jan 2023
    duckdb.connect().execute(
        """
        COPY (
            SELECT * FROM (VALUES
                (1, 1, 2, 1.0, 1, TIMESTAMP '2023-01-02 10:10', TIMESTAMP '2023-01-02 10:00', 1.2, 1.0, 10.5),
                (2, 1, 1, 1.0, 2, TIMESTAMP '2023-01-03 14:20', TIMESTAMP '2023-01-03 14:00', 3.4, 2.0, 20.0),
                (1, 2, 1, 1.0, 1, TIMESTAMP '2023-01-04 09:30', TIMESTAMP '2023-01-04 09:00', 2.1, 1.0, 15.0)
            ) AS t(VendorID, PULocationID, DOLocationID, RatecodeID, payment_type,
                   tpep_dropoff_datetime, tpep_pickup_datetime, trip_distance,
                   passenger_count, total_amount)
        ) TO 'data/raw/taxi_trips_2023-01.parquet' (FORMAT PARQUET)
        """
    )


def part_b_execute(trips, metrics, requests_mod):
    from dagster_duckdb import DuckDBResource

    workdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "course_verification_output")
    if os.path.exists(workdir):
        shutil.rmtree(workdir)
    os.makedirs(workdir, exist_ok=True)
    os.chdir(workdir)
    print(f"\nPART B — execute REAL course assets; outputs -> {workdir}")

    write_sample_inputs()
    database = DuckDBResource(database=os.path.join(workdir, "course.duckdb"))
    resources = {"database": database}

    # 1. ingest zones + monthly-partitioned trips into duckdb
    r = dg.materialize(
        [trips.taxi_zones, trips.taxi_trips], partition_key="2023-01-01", resources=resources
    )
    print(f"  [1] ingest taxi_zones + taxi_trips: success={r.success}")

    # 2. trips_by_week (weekly partition) -> data/outputs/trips_by_week.csv
    r = dg.materialize(
        [metrics.trips_by_week],
        partition_key="2023-01-01",
        resources=resources,
        selection=[metrics.trips_by_week],
    )
    print(f"  [2] trips_by_week: success={r.success}")

    # 3. manhattan_stats (geojson) -> manhattan_map (THE MAP png)
    r = dg.materialize([metrics.manhattan_stats, metrics.manhattan_map], resources=resources)
    print(f"  [3] manhattan_stats + manhattan_map: success={r.success}")

    # 4. adhoc_request (matplotlib chart png) with a run config
    r = dg.materialize(
        [requests_mod.adhoc_request],
        resources=resources,
        run_config=dg.RunConfig(
            ops={
                "adhoc_request": requests_mod.AdhocRequestConfig(
                    filename="adhoc_manhattan.json",
                    borough="Manhattan",
                    start_date="2023-01-01",
                    end_date="2023-02-01",
                )
            }
        ),
    )
    print(f"  [4] adhoc_request: success={r.success}")


def show_outputs():
    workdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "course_verification_output")
    print("\nGenerated outputs:")
    for root, _dirs, files in os.walk(workdir):
        for name in sorted(files):
            path = os.path.join(root, name)
            rel = os.path.relpath(path, workdir)
            print(f"  {rel:42s} {os.path.getsize(path):>8,} bytes")


def main():
    trips, metrics, requests_mod = part_a_imports()
    part_b_execute(trips, metrics, requests_mod)
    show_outputs()
    print("\nCOURSE VERIFICATION PASSED: full course graph (incl. map) runs on lightweight dagster")


if __name__ == "__main__":
    main()
