import importlib
import os
import tempfile
from typing import List, Mapping, Optional

import airflow
import pytz
from airflow.models.connection import Connection
from airflow.models.dag import DAG
from airflow.utils import db
from dagster import (
    Array,
    DagsterInvariantViolationError,
    Field,
    GraphDefinition,
    InitResourceContext,
    JobDefinition,
    ResourceDefinition,
    _check as check,
)
from dagster._core.definitions.utils import validate_tags
from dagster._core.instance import AIRFLOW_EXECUTION_DATE_STR, IS_AIRFLOW_INGEST_PIPELINE_STR
from dateutil.parser import parse

from dagster_airflow.airflow_dag_converter import get_graph_definition_args
from dagster_airflow.utils import (
    Locker,
    create_airflow_connections,
    is_airflow_2,
    normalized_name,
    serialize_connections,
)

# pylint: disable=no-name-in-module,import-error
if is_airflow_2():
    from airflow.utils.state import DagRunState
    from airflow.utils.types import DagRunType
else:
    from airflow.utils.state import State
# pylint: enable=no-name-in-module,import-error


def make_dagster_job_from_airflow_dag(
    dag: DAG,
    tags: Optional[Mapping[str, str]] = None,
    unique_id: Optional[int] = None,
    connections: Optional[List[Connection]] = None,
):
    """Construct a Dagster job corresponding to a given Airflow DAG.

    Tasks in the resulting job will execute the ``execute()`` method on the corresponding
    Airflow Operator. Dagster, any dependencies required by Airflow Operators, and the module
    containing your DAG definition must be available in the Python environment within which your
    Dagster solids execute.

    To set Airflow's ``execution_date`` for use with Airflow Operator's ``execute()`` methods,
    either:

    1. (Best for ad hoc runs) Execute job directly. This will set execution_date to the
        time (in UTC) of the run.

    2. Add ``{'airflow_execution_date': utc_date_string}`` to the job tags. This will override
        behavior from (1).

        .. code-block:: python

            my_dagster_job = make_dagster_job_from_airflow_dag(
                    dag=dag,
                    tags={'airflow_execution_date': utc_execution_date_str}
            )
            my_dagster_job.execute_in_process()

    3. (Recommended) Add ``{'airflow_execution_date': utc_date_string}`` to the run tags,
        such as in the Dagit UI. This will override behavior from (1) and (2)


    We apply normalized_name() to the dag id and task ids when generating job name and op
    names to ensure that names conform to Dagster's naming conventions.

    Args:
        dag (DAG): The Airflow DAG to compile into a Dagster job
        tags (Dict[str, Field]): Job tags. Optionally include
            `tags={'airflow_execution_date': utc_date_string}` to specify execution_date used within
            execution of Airflow Operators.
        unique_id (int): If not None, this id will be postpended to generated op names. Used by
            framework authors to enforce unique op names within a repo.
        connections (List[Connection]): List of Airflow Connections to be created in the Ephemeral
            Airflow DB, if use_emphemeral_airflow_db is False this will be ignored.

    Returns:
        JobDefinition: The generated Dagster job

    """
    check.inst_param(dag, "dag", DAG)
    tags = check.opt_mapping_param(tags, "tags")
    unique_id = check.opt_int_param(unique_id, "unique_id")
    connections = check.opt_list_param(connections, "connections", of_type=Connection)

    mutated_tags = dict(tags)
    if IS_AIRFLOW_INGEST_PIPELINE_STR not in tags:
        mutated_tags[IS_AIRFLOW_INGEST_PIPELINE_STR] = "true"

    mutated_tags = validate_tags(mutated_tags)

    node_dependencies, node_defs = get_graph_definition_args(dag=dag, unique_id=unique_id)

    serialized_connections = serialize_connections(connections)

    def airflow_db(context: InitResourceContext):
        airflow_home_path = os.path.join(tempfile.gettempdir(), f"dagster_airflow_{context.run_id}")
        os.environ["AIRFLOW_HOME"] = airflow_home_path
        os.makedirs(airflow_home_path, exist_ok=True)
        with Locker(airflow_home_path):
            airflow_initialized = os.path.exists(f"{airflow_home_path}/airflow.db")
            # because AIRFLOW_HOME has been overriden airflow needs to be reloaded
            if is_airflow_2():
                importlib.reload(airflow.configuration)
                importlib.reload(airflow.settings)
                importlib.reload(airflow)
            else:
                importlib.reload(airflow)
            if not airflow_initialized:
                db.initdb()
                create_airflow_connections(
                    [Connection(**c) for c in context.resource_config["connections"]]
                )
            dag = context.resources.dag
            run_tags = context.dagster_run.tags if context.dagster_run else {}
            if AIRFLOW_EXECUTION_DATE_STR in run_tags:
                # for airflow DAGs that have not been turned into SDAs
                execution_date_str = run_tags.get(AIRFLOW_EXECUTION_DATE_STR)
                if not execution_date_str:
                    raise DagsterInvariantViolationError(
                        "Expected execution_date_str to be set in run tags."
                    )
                check.str_param(execution_date_str, "execution_date_str")
                try:
                    execution_date = parse(execution_date_str)
                    execution_date = execution_date.replace(tzinfo=pytz.timezone(dag.timezone.name))
                except ValueError:
                    raise DagsterInvariantViolationError(
                        'Could not parse execution_date "{execution_date_str}". Please use datetime'
                        " format compatible with  dateutil.parser.parse.".format(
                            execution_date_str=execution_date_str,
                        )
                    )
                except OverflowError:
                    raise DagsterInvariantViolationError(
                        'Date "{execution_date_str}" exceeds the largest valid C integer on the'
                        " system.".format(
                            execution_date_str=execution_date_str,
                        )
                    )
            elif "dagster/partition" in run_tags:
                # for airflow DAGs that have been turned into SDAs
                execution_date_str = run_tags.get("dagster/partition")
                if not execution_date_str:
                    raise DagsterInvariantViolationError("dagster/partition is not set")
                execution_date = parse(execution_date_str)
                execution_date = execution_date.replace(tzinfo=pytz.timezone(dag.timezone.name))
            else:
                raise DagsterInvariantViolationError(
                    'Could not find "{AIRFLOW_EXECUTION_DATE_STR}" in tags "{tags}". Please '
                    'add "{AIRFLOW_EXECUTION_DATE_STR}" to tags before executing'.format(
                        AIRFLOW_EXECUTION_DATE_STR=AIRFLOW_EXECUTION_DATE_STR,
                        tags=run_tags,
                    )
                )

            dagrun = dag.get_dagrun(execution_date=execution_date)
            if not dagrun:
                if is_airflow_2():
                    dagrun = dag.create_dagrun(
                        state=DagRunState.RUNNING,
                        execution_date=execution_date,
                        run_type=DagRunType.MANUAL,
                    )
                else:
                    dagrun = dag.create_dagrun(
                        run_id=f"dagster_airflow_run_{execution_date}",
                        state=State.RUNNING,
                        execution_date=execution_date,
                    )
        return {
            "dag": dag,
            "dagrun": dagrun,
        }

    dag_resource = ResourceDefinition.hardcoded_resource(value=dag, description="DAG model")
    airflow_db_resource_def = ResourceDefinition(
        resource_fn=airflow_db,
        required_resource_keys={"dag"},
        config_schema={
            "connections": Field(
                Array(inner_type=dict),
                default_value=serialized_connections,
                is_required=False,
            ),
        },
        description="Airflow DB resource",
    )

    graph_def = GraphDefinition(
        name=normalized_name(dag.dag_id),
        description="",
        node_defs=node_defs,
        dependencies=node_dependencies,
        tags=mutated_tags,
    )

    job_def = JobDefinition(
        name=normalized_name(dag.dag_id),
        description="",
        resource_defs={"airflow_db": airflow_db_resource_def, "dag": dag_resource},
        graph_def=graph_def,
        tags=mutated_tags,
        metadata={},
        op_retry_policy=None,
        version_strategy=None,
    )
    return job_def
