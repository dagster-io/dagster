# ruff: noqa: T201
import argparse
import os
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Generator, List, Tuple

import dagster._check as check
from dagster import Definitions, RepositoryDefinition, build_sensor_context
from dagster._core.instance import DagsterInstance
from dagster._core.test_utils import environ
from dagster_airlift.core.airflow_instance import AirflowInstance
from dagster_airlift.test.shared_fixtures import stand_up_airflow

from perf_harness.shared.constants import CONSTANTS_FILE, get_perf_output_file
from perf_harness.shared.utils import scaffold_proxied_state

MAKEFILE_DIR = Path(__file__).parent.parent
DAGSTER_HOME = MAKEFILE_DIR / ".dagster_home"


@contextmanager
def modify_constants(num_dags, num_tasks, num_assets) -> Generator[None, None, None]:
    # Read the original content
    with open(CONSTANTS_FILE, "r") as f:
        original_content = f.read()

    # Write new constants
    modified_content = (
        f"NUM_DAGS {num_dags}\nNUM_TASKS {num_tasks}\nNUM_ASSETS_PER_TASK {num_assets}\n"
    )

    # Write the modified content
    with open(CONSTANTS_FILE, "w") as f:
        f.write(modified_content)

    try:
        # Yield control back to the caller
        yield
    finally:
        # Restore the original content
        with open(CONSTANTS_FILE, "w") as f:
            f.write(original_content)


def main() -> None:
    lines = []
    parser = argparse.ArgumentParser(description="Performance scenario testing for airlift")
    parser.add_argument("num_dags", type=int, help="Number of DAGs to generate")
    parser.add_argument("num_tasks", type=int, help="Number of tasks per DAG")
    parser.add_argument("num_assets", type=int, help="Number of assets per task")

    args = parser.parse_args()

    num_dags = check.int_param(args.num_dags, "num_dags")
    num_tasks = check.int_param(args.num_tasks, "num_tasks")
    num_assets = check.int_param(args.num_assets, "num_assets")

    with modify_constants(num_dags, num_tasks, num_assets), environ(
        {"DAGSTER_HOME": str(DAGSTER_HOME)}
    ):
        print("Scaffolding proxied state...")
        scaffold_proxied_state(num_dags=num_dags, num_tasks=num_tasks, proxied_state=True)

        print("Importing airflow defs...")
        from perf_harness.airflow_dags.dags import (
            import_time,
            mark_as_dagster_time,
            total_time as total_load_time,
        )

        lines.append(f"Total airflow dags load time: {total_load_time:.4f} seconds\n")
        lines.append(f"Airflow defs import time: {import_time:.4f} seconds\n")
        lines.append(f"Proxying to dagster time: {mark_as_dagster_time:.4f} seconds\n")

        print("Initializing airflow...")
        # Take in as an argument the number of tasks and the number of dags.
        # Create an ephemeral file where the results will be written, and assign it in shared.constants.py
        # Stand up airflow.
        # Stand up dagster at each stage (peer, observe, migrate), wiping .dagster_home in between.
        # At each stage, time how long initial load takes
        # Then, time how long subsequent load takes
        # Run the test sensor graphql mutation and time how long it takes.
        # Write all results to the ephemeral file.

        airflow_setup_time = time.time()
        subprocess.run(
            ["make", "setup_local_env"], check=True, cwd=MAKEFILE_DIR, stdout=subprocess.DEVNULL
        )
        airflow_setup_completion_time = time.time()
        lines.append(
            f"Airflow setup time: {airflow_setup_completion_time - airflow_setup_time:.4f} seconds\n"
        )

        print("Standing up airflow...")
        start_airflow_standup_time = time.time()
        with stand_up_airflow(
            env=os.environ,
            airflow_cmd=["make", "run_airflow"],
            cwd=MAKEFILE_DIR,
            stdout_channel=subprocess.DEVNULL,
        ):
            module_name_to_defs_and_instance = {}
            finished_airflow_standup_time = time.time()
            lines.append(
                f"Airflow standup time: {finished_airflow_standup_time - start_airflow_standup_time:.4f} seconds\n"
            )
            print("Loading peering defs...")
            peered_defs_import_start_time = time.time()
            from perf_harness.dagster_defs.peer import defs

            peered_defs_import_end_time = time.time()
            peered_defs_import_time = peered_defs_import_end_time - peered_defs_import_start_time
            lines.append(f"Peered defs import time: {peered_defs_import_time:.4f} seconds\n")
            from perf_harness.dagster_defs.peer import airflow_instance

            module_name_to_defs_and_instance["peer"] = (defs, airflow_instance)

            print("Loading observing defs...")
            observe_defs_import_start_time = time.time()
            from perf_harness.dagster_defs.observe import defs

            observe_defs_import_end_time = time.time()
            observe_defs_import_time = observe_defs_import_end_time - observe_defs_import_start_time
            lines.append(f"Observed defs import time: {observe_defs_import_time:.4f} seconds\n")
            from perf_harness.dagster_defs.observe import airflow_instance

            module_name_to_defs_and_instance["observe"] = (defs, airflow_instance)

            print("Loading migrated defs...")
            migrate_defs_import_start_time = time.time()
            from perf_harness.dagster_defs.migrate import defs

            migrate_defs_import_end_time = time.time()
            migrate_defs_import_time = migrate_defs_import_end_time - migrate_defs_import_start_time
            lines.append(f"Migrate defs import time: {migrate_defs_import_time:.4f} seconds\n")
            from perf_harness.dagster_defs.migrate import airflow_instance

            module_name_to_defs_and_instance["migrate"] = (defs, airflow_instance)

            print("Running performance tests across modules...")
            lines.extend(
                run_suite_for_defs(
                    module_name_to_defs_and_instance=module_name_to_defs_and_instance,
                    num_dags=num_dags,
                    instance=DagsterInstance.get(),
                )
            )

        with open(get_perf_output_file(), "w") as f:
            f.writelines(lines)
    print("Performance harness completed.")


def run_suite_for_defs(
    *,
    module_name_to_defs_and_instance: Dict[str, Tuple[Definitions, AirflowInstance]],
    num_dags: int,
    instance: DagsterInstance,
) -> List[str]:
    lines = []
    module_name_to_repo_def_and_instance: Dict[
        str, Tuple[RepositoryDefinition, AirflowInstance]
    ] = {}
    for module_name, (defs, af_instance) in module_name_to_defs_and_instance.items():
        defs_initial_load_time = time.time()
        print(f"Loading cacheable assets for {module_name} defs...")
        repo_def = defs.get_repository_def()
        defs_initial_load_completion_time = time.time()
        lines.append(
            f"{module_name} defs initial load time: {defs_initial_load_completion_time - defs_initial_load_time:.4f} seconds\n"
        )
        module_name_to_repo_def_and_instance[module_name] = (repo_def, af_instance)

    print("Running sensor ticks with no runs...")
    for module_name, (repo_def, af_instance) in module_name_to_repo_def_and_instance.items():
        sensor_def = repo_def.get_sensor_def("my_airflow_instance__airflow_dag_status_sensor")
        print(f"Running {module_name} sensor ticks...")
        sensor_tick_no_runs_start_time = time.time()
        sensor_def(build_sensor_context(repository_def=repo_def, instance=instance))
        sensor_tick_no_runs_end_time = time.time()

        lines.append(
            f"{module_name} sensor tick with no runs time: {sensor_tick_no_runs_end_time - sensor_tick_no_runs_start_time:.4f} seconds\n"
        )

    print("Running dag once...")
    run_id = af_instance.trigger_dag("dag_0")
    af_instance.wait_for_run_completion("dag_0", run_id, timeout=400)
    print("Dag run completed.")
    print("Running sensor ticks with single run...")
    for module_name, (repo_def, af_instance) in module_name_to_repo_def_and_instance.items():
        sensor_def = repo_def.get_sensor_def("my_airflow_instance__airflow_dag_status_sensor")
        sensor_tick_with_single_run_start_time = time.time()
        sensor_def(build_sensor_context(repository_def=repo_def, instance=instance))
        sensor_tick_with_single_run_end_time = time.time()
        lines.append(
            f"{module_name} sensor tick with single run time: {sensor_tick_with_single_run_end_time - sensor_tick_with_single_run_start_time:.4f} seconds\n"
        )
    print("Deleting run...")
    # Delete that run. Then add a run to every dag.
    af_instance.delete_run("dag_0", run_id)
    print("Running every dag...")
    newly_added_runs = {}
    for i in range(num_dags):
        newly_added_runs[f"dag_{i}"] = af_instance.trigger_dag(f"dag_{i}")
    completed_runs = []
    while len(completed_runs) < num_dags:
        for dag_id, run_id in newly_added_runs.items():
            if run_id in completed_runs:
                continue
            run_state = af_instance.get_run_state(dag_id, run_id)
            if run_state == "success":
                completed_runs.append(run_id)
                continue
            if run_state == "failed":
                raise Exception("A run failed.")
    print("All runs completed.")
    print("Running sensor ticks with all runs...")
    for module_name, (repo_def, af_instance) in module_name_to_repo_def_and_instance.items():
        sensor_def = repo_def.get_sensor_def("my_airflow_instance__airflow_dag_status_sensor")
        sensor_tick_with_all_runs_start_time = time.time()
        sensor_def(build_sensor_context(repository_def=repo_def, instance=instance))
        sensor_tick_with_all_runs_end_time = time.time()
        lines.append(
            f"{module_name} sensor tick with {num_dags} runs time: {sensor_tick_with_all_runs_end_time - sensor_tick_with_all_runs_start_time:.4f} seconds\n"
        )
    # Delete all runs.
    for dag_id, run_id in newly_added_runs.items():
        af_instance.delete_run(dag_id, run_id)
    print("Deleted all runs.")
    return lines


if __name__ == "__main__":
    main()
