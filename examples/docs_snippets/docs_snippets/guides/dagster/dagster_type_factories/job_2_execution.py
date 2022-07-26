from .job_2 import generate_trip_distribution_plot

# execution_1

generate_trip_distribution_plot.execute_in_process()
# => ...
# => dagster._core.errors.DagsterTypeCheckDidNotPass: Type check failed for step output "result" - expected type "TripsDataFrame".
# => ...

# execution_2

generate_trip_distribution_plot.execute_in_process(
    run_config={"ops": {"load_trips": {"config": {"clean": True}}}}
)
# => ...
# => 2021-11-11 19:54:26 - dagster - DEBUG - generate_trip_plots - 3e00e9e3-27f3-490e-b1bd-ec17b92e5599 - 28168 - RUN_SUCCESS - Finished execution of run for "generate_trip_plots".
