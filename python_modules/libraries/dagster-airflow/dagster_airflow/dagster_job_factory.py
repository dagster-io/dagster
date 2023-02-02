import importlib
import os
import tempfile

import airflow
import dateutil
import pytz
from airflow import __version__ as airflow_version
from airflow.models.connection import Connection
from airflow.models.dag import DAG
from airflow.models.dagbag import DagBag
from airflow.utils import db
from dagster import (
    Array,
    DagsterInvariantViolationError,
    Definitions,
    Field,
    GraphDefinition,
    JobDefinition,
    _check as check,
    resource,
)
from dagster._core.definitions.utils import validate_tags
from dagster._core.instance import AIRFLOW_EXECUTION_DATE_STR, IS_AIRFLOW_INGEST_PIPELINE_STR

from dagster_airflow.airflow_dag_converter import get_graph_definition_args
from dagster_airflow.dagster_schedule_factory import make_dagster_schedule_from_airflow_dag
from dagster_airflow.patch_airflow_example_dag import patch_airflow_example_dag
from dagster_airflow.utils import (
    DagsterAirflowError,
    Locker,
    contains_duplicate_task_names,
    create_airflow_connections,
    normalized_name,
    serialize_connections,
)

# pylint: disable=no-name-in-module,import-error
if str(airflow_version) >= "2.0.0":
    from airflow.utils.state import DagRunState
    from airflow.utils.types import DagRunType
else:
    from airflow.utils.state import State
# pylint: enable=no-name-in-module,import-error


def make_dagster_job_from_airflow_dag(
    dag,
    tags=None,
    unique_id=None,
    connections=None,
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
    tags = check.opt_dict_param(tags, "tags")
    unique_id = check.opt_int_param(unique_id, "unique_id")
    connections = check.opt_list_param(connections, "connections", of_type=Connection)

    connections = check.opt_list_param(connections, "connections", of_type=Connection)

    if IS_AIRFLOW_INGEST_PIPELINE_STR not in tags:
        tags[IS_AIRFLOW_INGEST_PIPELINE_STR] = "true"

    tags = validate_tags(tags)

    node_dependencies, node_defs = get_graph_definition_args(dag=dag, unique_id=unique_id)

    serialized_connections = serialize_connections(connections)

    @resource(
        config_schema={
            "dag_location": Field(str, default_value=dag.fileloc),
            "dag_id": Field(str, default_value=dag.dag_id),
            "connections": Field(
                Array(inner_type=dict),
                default_value=serialized_connections,
                is_required=False,
            ),
        }
    )
    def airflow_db(context):
        airflow_home_path = os.path.join(tempfile.gettempdir(), f"dagster_airflow_{context.run_id}")
        os.environ["AIRFLOW_HOME"] = airflow_home_path
        os.makedirs(airflow_home_path, exist_ok=True)
        with Locker(airflow_home_path):
            airflow_initialized = os.path.exists(f"{airflow_home_path}/airflow.db")
            # because AIRFLOW_HOME has been overriden airflow needs to be reloaded
            if airflow_version >= "2.0.0":
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

            dag_bag = airflow.models.dagbag.DagBag(
                dag_folder=context.resource_config["dag_location"], include_examples=False
            )
            dag = dag_bag.get_dag(context.resource_config["dag_id"])
            if AIRFLOW_EXECUTION_DATE_STR in context.dagster_run.tags:
                # for airflow DAGs that have not been turned into SDAs
                execution_date_str = context.dagster_run.tags.get(AIRFLOW_EXECUTION_DATE_STR)
                check.str_param(execution_date_str, "execution_date_str")
                try:
                    execution_date = dateutil.parser.parse(execution_date_str)
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
            elif "dagster/partition" in context.dagster_run.tags:
                # for airflow DAGs that have been turned into SDAs
                execution_date_str = context.dagster_run.tags.get("dagster/partition")
                execution_date = dateutil.parser.parse(execution_date_str)
                execution_date = execution_date.replace(tzinfo=pytz.timezone(dag.timezone.name))
            else:
                raise DagsterInvariantViolationError(
                    'Could not find "{AIRFLOW_EXECUTION_DATE_STR}" in tags "{tags}". Please '
                    'add "{AIRFLOW_EXECUTION_DATE_STR}" to tags before executing'.format(
                        AIRFLOW_EXECUTION_DATE_STR=AIRFLOW_EXECUTION_DATE_STR,
                        tags=context.dagster_run.tags,
                    )
                )

            dagrun = dag.get_dagrun(execution_date=execution_date)
            if not dagrun:
                if airflow_version >= "2.0.0":
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

    graph_def = GraphDefinition(
        name=normalized_name(dag.dag_id),
        description="",
        node_defs=node_defs,
        dependencies=node_dependencies,
        tags=tags,
    )

    job_def = JobDefinition(
        name=normalized_name(dag.dag_id),
        description="",
        resource_defs={"airflow_db": airflow_db},
        graph_def=graph_def,
        tags=tags,
        metadata={},
        op_retry_policy=None,
        version_strategy=None,
    )
    return job_def


def make_dagster_definitions_from_airflow_dag_bag(
    dag_bag,
    connections=None,
):
    """Construct a Dagster definition corresponding to Airflow DAGs in DagBag.

    Usage:
        Create `make_dagster_definition.py`:
            from dagster_airflow import make_dagster_definition_from_airflow_dag_bag
            from airflow_home import my_dag_bag

            def make_definition_from_dag_bag():
                return make_dagster_definition_from_airflow_dag_bag(my_dag_bag)

        Use Definitions as usual, for example:
            `dagit -f path/to/make_dagster_definition.py`

    Args:
        dag_bag (DagBag): Airflow DagBag Model
        connections (List[Connection]): List of Airflow Connections to be created in the Ephemeral
            Airflow DB, if use_emphemeral_airflow_db is False this will be ignored.

    Returns:
        Definitions
    """
    schedules, jobs = make_schedules_and_jobs_from_airflow_dag_bag(
        dag_bag,
        connections,
    )

    return Definitions(
        schedules=schedules,
        jobs=jobs,
    )


def make_dagster_definitions_from_airflow_dags_path(
    dag_path,
    safe_mode=True,
    connections=None,
):
    """Construct a Dagster repository corresponding to Airflow DAGs in dag_path.

    Usage:
        Create ``make_dagster_definitions.py``:

        .. code-block:: python

            from dagster_airflow import make_dagster_definitions_from_airflow_dags_path

            def make_definitions_from_dir():
                return make_dagster_definitions_from_airflow_dags_path(
                    '/path/to/dags/',
                )

        Use RepositoryDefinition as usual, for example:
        ``dagit -f path/to/make_dagster_repo.py -n make_repo_from_dir``

    Args:
        dag_path (str): Path to directory or file that contains Airflow Dags
        include_examples (bool): True to include Airflow's example DAGs. (default: False)
        safe_mode (bool): True to use Airflow's default heuristic to find files that contain DAGs
            (ie find files that contain both b'DAG' and b'airflow') (default: True)
        connections (List[Connection]): List of Airflow Connections to be created in the Ephemeral
            Airflow DB, if use_emphemeral_airflow_db is False this will be ignored.

    Returns:
        Definitions
    """
    check.str_param(dag_path, "dag_path")
    check.bool_param(safe_mode, "safe_mode")
    connections = check.opt_list_param(connections, "connections", of_type=Connection)
    # add connections to airflow so that dag evaluation works
    create_airflow_connections(connections)
    try:
        dag_bag = DagBag(
            dag_folder=dag_path,
            include_examples=False,  # Exclude Airflow example dags
            safe_mode=safe_mode,
        )
    except Exception:
        raise DagsterAirflowError("Error initializing airflow.models.dagbag object with arguments")

    return make_dagster_definitions_from_airflow_dag_bag(
        dag_bag=dag_bag,
        connections=connections,
    )


def make_dagster_definitions_from_airflow_example_dags():
    """Construct a Dagster repository for Airflow's example DAGs.

    Usage:

        Create `make_dagster_definitions.py`:
            from dagster_airflow import make_dagster_definitions_from_airflow_example_dags

            def make_airflow_example_dags():
                return make_dagster_definitions_from_airflow_example_dags()

        Use Definitions as usual, for example:
            `dagit -f path/to/make_dagster_definitions.py`

    Args:

    Returns:
        Definitions
    """
    dag_bag = DagBag(
        dag_folder="some/empty/folder/with/no/dags",  # prevent defaulting to settings.DAGS_FOLDER
        include_examples=True,
    )

    # There is a bug in Airflow v1 where the python_callable for task
    # 'search_catalog' is missing a required position argument '_'. It is fixed in airflow v2
    patch_airflow_example_dag(dag_bag)

    return make_dagster_definitions_from_airflow_dag_bag(dag_bag=dag_bag)


def make_schedules_and_jobs_from_airflow_dag_bag(
    dag_bag,
    connections=None,
):
    """Construct Dagster Schedules and Jobs corresponding to Airflow DagBag.

    Args:
        dag_bag (DagBag): Airflow DagBag Model
        connections (List[Connection]): List of Airflow Connections to be created in the Ephemeral
            Airflow DB, if use_emphemeral_airflow_db is False this will be ignored.

    Returns:
        - List[ScheduleDefinition]: The generated Dagster Schedules
        - List[JobDefinition]: The generated Dagster Jobs
    """
    check.inst_param(dag_bag, "dag_bag", DagBag)
    connections = check.opt_list_param(connections, "connections", of_type=Connection)

    use_unique_id = contains_duplicate_task_names(dag_bag)

    job_defs = []
    schedule_defs = []
    count = 0
    # To enforce predictable iteration order
    sorted_dag_ids = sorted(dag_bag.dag_ids)
    for dag_id in sorted_dag_ids:
        dag = dag_bag.dags.get(dag_id)
        if not use_unique_id:
            job_def = make_dagster_job_from_airflow_dag(
                dag=dag,
                tags=None,
                connections=connections,
            )
        else:
            job_def = make_dagster_job_from_airflow_dag(
                dag=dag,
                tags=None,
                unique_id=count,
                connections=connections,
            )
            count += 1
        schedule_def = make_dagster_schedule_from_airflow_dag(
            dag=dag,
            job_def=job_def,
        )
        if schedule_def:
            schedule_defs.append(schedule_def)
        else:
            job_defs.append(job_def)

    return schedule_defs, job_defs
