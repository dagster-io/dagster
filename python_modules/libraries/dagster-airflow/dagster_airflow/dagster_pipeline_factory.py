import datetime
import importlib
import logging
import os
import sys
import tempfile
from contextlib import contextmanager, nullcontext
from unittest.mock import patch

import airflow
import dateutil
import lazy_object_proxy
import pendulum
from airflow import __version__ as airflow_version
from airflow.models import TaskInstance
from airflow.models.baseoperator import BaseOperator
from airflow.models.connection import Connection
from airflow.models.dag import DAG
from airflow.models.dagbag import DagBag
from airflow.settings import LOG_FORMAT
from airflow.utils import db
from dagster import (
    Array,
    DagsterInvariantViolationError,
    DependencyDefinition,
    Field,
    In,
    JobDefinition,
    MultiDependencyDefinition,
    Nothing,
    Out,
    ScheduleDefinition,
    _check as check,
    op,
    repository,
    resource,
)
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.definitions.utils import VALID_NAME_REGEX, validate_tags
from dagster._core.instance import AIRFLOW_EXECUTION_DATE_STR, IS_AIRFLOW_INGEST_PIPELINE_STR
from dagster._legacy import ModeDefinition, PipelineDefinition
from dagster._utils.schedules import is_valid_cron_schedule

from dagster_airflow.patch_airflow_example_dag import patch_airflow_example_dag

# pylint: disable=no-name-in-module,import-error
if str(airflow_version) >= "2.0.0":
    from airflow.utils.session import create_session
    from airflow.utils.state import DagRunState
    from airflow.utils.types import DagRunType
else:
    from airflow.utils.db import create_session
    from airflow.utils.state import State
# pylint: enable=no-name-in-module,import-error


class DagsterAirflowError(Exception):
    pass


if os.name == "nt":
    import msvcrt  # pylint: disable=import-error

    def portable_lock(fp):
        fp.seek(0)
        msvcrt.locking(fp.fileno(), msvcrt.LK_LOCK, 1)

    def portable_unlock(fp):
        fp.seek(0)
        msvcrt.locking(fp.fileno(), msvcrt.LK_UNLCK, 1)

else:
    import fcntl

    def portable_lock(fp):
        fcntl.flock(fp.fileno(), fcntl.LOCK_EX)

    def portable_unlock(fp):
        fcntl.flock(fp.fileno(), fcntl.LOCK_UN)


class Locker:
    def __init__(self, lock_file_path="."):
        self.lock_file_path = lock_file_path
        self.fp = None

    def __enter__(self):
        self.fp = open(f"{self.lock_file_path}/lockfile.lck", "w+", encoding="utf-8")
        portable_lock(self.fp)

    def __exit__(self, _type, value, tb):
        portable_unlock(self.fp)
        self.fp.close()


def _create_airflow_connections(connections):
    with create_session() as session:
        for connection in connections:
            if session.query(Connection).filter(Connection.conn_id == connection.conn_id).first():
                logging.info(
                    f"Could not import connection {connection.conn_id}: connection already exists."
                )
                continue

            session.add(connection)
            session.commit()
            logging.info(f"Imported connection {connection.conn_id}")


def _contains_duplicate_task_names(dag_bag):
    check.inst_param(dag_bag, "dag_bag", DagBag)
    seen_task_names = set()

    # To enforce predictable iteration order
    sorted_dag_ids = sorted(dag_bag.dag_ids)
    for dag_id in sorted_dag_ids:
        dag = dag_bag.dags.get(dag_id)
        for task in dag.tasks:
            if task.task_id in seen_task_names:
                return True
            else:
                seen_task_names.add(task.task_id)
    return False


def _make_schedules_and_jobs_from_airflow_dag_bag(
    dag_bag,
    use_airflow_template_context=False,
    mock_xcom=False,
    use_ephemeral_airflow_db=True,
    connections=None,
):
    """Construct Dagster Schedules and Jobs corresponding to Airflow DagBag.

    Args:
        dag_bag (DagBag): Airflow DagBag Model
        use_airflow_template_context (bool): If True, will call get_template_context() on the
            Airflow TaskInstance model which requires and modifies the DagRun table. The use_airflow_template_context
            setting is ignored if use_ephemeral_airflow_db is True.
            (default: False)
        mock_xcom (bool): If True, dagster will mock out all calls made to xcom, features that
            depend on xcom may not work as expected. (default: False)
        use_ephemeral_airflow_db (bool): If True, dagster will create an ephemeral sqlite airflow
            database for each run. (default: False)
        connections (List[Connection]): List of Airflow Connections to be created in the Ephemeral
            Airflow DB, if use_emphemeral_airflow_db is False this will be ignored.

    Returns:
        - List[ScheduleDefinition]: The generated Dagster Schedules
        - List[JobDefinition]: The generated Dagster Jobs
    """
    check.inst_param(dag_bag, "dag_bag", DagBag)
    check.bool_param(use_airflow_template_context, "use_airflow_template_context")
    mock_xcom = check.opt_bool_param(mock_xcom, "mock_xcom")
    use_ephemeral_airflow_db = check.opt_bool_param(
        use_ephemeral_airflow_db, "use_ephemeral_airflow_db"
    )
    connections = check.opt_list_param(connections, "connections", of_type=Connection)

    use_unique_id = _contains_duplicate_task_names(dag_bag)

    job_defs = []
    schedule_defs = []
    count = 0
    # To enforce predictable iteration order
    sorted_dag_ids = sorted(dag_bag.dag_ids)
    for dag_id in sorted_dag_ids:
        dag = dag_bag.dags.get(dag_id)
        if not use_unique_id:
            pipeline_def = make_dagster_pipeline_from_airflow_dag(
                dag=dag,
                tags=None,
                use_airflow_template_context=use_airflow_template_context,
                mock_xcom=mock_xcom,
                use_ephemeral_airflow_db=use_ephemeral_airflow_db,
                connections=connections,
            )
        else:
            pipeline_def = make_dagster_pipeline_from_airflow_dag(
                dag=dag,
                tags=None,
                use_airflow_template_context=use_airflow_template_context,
                unique_id=count,
                mock_xcom=mock_xcom,
                use_ephemeral_airflow_db=use_ephemeral_airflow_db,
                connections=connections,
            )
            count += 1
        # pass in tags manually because pipeline_def.graph doesn't have it threaded
        job_def = pipeline_def.graph.to_job(
            tags={**pipeline_def.tags},
            resource_defs={
                "airflow_db": pipeline_def.mode_definitions[0].resource_defs["airflow_db"]
            }
            if use_ephemeral_airflow_db
            else {},
        )
        schedule_def = make_dagster_schedule_from_airflow_dag(
            dag=dag,
            job_def=job_def,
        )
        if schedule_def:
            schedule_defs.append(schedule_def)
        else:
            job_defs.append(job_def)

    return schedule_defs, job_defs


def make_dagster_repo_from_airflow_dag_bag(
    dag_bag,
    repo_name,
    use_airflow_template_context=False,
    mock_xcom=False,
    use_ephemeral_airflow_db=False,
    connections=None,
):
    """Construct a Dagster repository corresponding to Airflow DAGs in DagBag.

    Usage:
        Create `make_dagster_repo.py`:
            from dagster_airflow.dagster_pipeline_factory import make_dagster_repo_from_airflow_dag_bag
            from airflow_home import my_dag_bag

            def make_repo_from_dag_bag():
                return make_dagster_repo_from_airflow_dag_bag(my_dag_bag, 'my_repo_name')

        Use RepositoryDefinition as usual, for example:
            `dagit -f path/to/make_dagster_repo.py -n make_repo_from_dag_bag`

    Args:
        dag_bag (DagBag): Airflow DagBag Model
        repo_name (str): Name for generated RepositoryDefinition
        use_airflow_template_context (bool): If True, will call get_template_context() on the
            Airflow TaskInstance model which requires and modifies the DagRun table. The use_airflow_template_context
            setting is ignored if use_ephemeral_airflow_db is True.
            (default: False)
        mock_xcom (bool): If True, dagster will mock out all calls made to xcom, features that
            depend on xcom may not work as expected. (default: False)
        use_ephemeral_airflow_db (bool): If True, dagster will create an ephemeral sqlite airflow
            database for each run. (default: False)
        connections (List[Connection]): List of Airflow Connections to be created in the Ephemeral
            Airflow DB, if use_emphemeral_airflow_db is False this will be ignored.

    Returns:
        RepositoryDefinition
    """
    check.inst_param(dag_bag, "dag_bag", DagBag)
    check.str_param(repo_name, "repo_name")
    check.bool_param(use_airflow_template_context, "use_airflow_template_context")
    mock_xcom = check.opt_bool_param(mock_xcom, "mock_xcom")
    use_ephemeral_airflow_db = check.opt_bool_param(
        use_ephemeral_airflow_db, "use_ephemeral_airflow_db"
    )
    connections = check.opt_list_param(connections, "connections", of_type=Connection)

    schedules, jobs = _make_schedules_and_jobs_from_airflow_dag_bag(
        dag_bag,
        use_airflow_template_context,
        mock_xcom,
        use_ephemeral_airflow_db,
        connections,
    )

    @repository(name=repo_name)
    def _repo():
        return [jobs, schedules]

    return _repo


def make_dagster_schedule_from_airflow_dag(dag, job_def):
    """Construct a Dagster schedule corresponding to an Airflow DAG.

    Args:
        dag (DAG): Airflow DAG
        job_def (JobDefinition): Dagster pipeline corresponding to Airflow DAG

    Returns:
        ScheduleDefinition
    """
    check.inst_param(dag, "dag", DAG)
    check.inst_param(job_def, "job_def", JobDefinition)

    cron_schedule = dag.normalized_schedule_interval
    schedule_description = dag.description

    if isinstance(dag.normalized_schedule_interval, str) and is_valid_cron_schedule(cron_schedule):
        return ScheduleDefinition(
            job=job_def,
            cron_schedule=cron_schedule,
            description=schedule_description,
            execution_timezone=dag.timezone.name,
        )


def make_dagster_repo_from_airflow_example_dags(
    repo_name="airflow_example_dags_repo", use_ephemeral_airflow_db=True
):
    """Construct a Dagster repository for Airflow's example DAGs.

    Usage:

        Create `make_dagster_repo.py`:
            from dagster_airflow.dagster_pipeline_factory import make_dagster_repo_from_airflow_example_dags

            def make_airflow_example_dags():
                return make_dagster_repo_from_airflow_example_dags()

        Use RepositoryDefinition as usual, for example:
            `dagit -f path/to/make_dagster_repo.py -n make_airflow_example_dags`

    Args:
        repo_name (str): Name for generated RepositoryDefinition
        use_ephemeral_airflow_db (bool): If True, dagster will create an ephemeral sqlite airflow
            database for each run. (default: True)

    Returns:
        RepositoryDefinition
    """
    dag_bag = DagBag(
        dag_folder="some/empty/folder/with/no/dags",  # prevent defaulting to settings.DAGS_FOLDER
        include_examples=True,
    )

    # There is a bug in Airflow v1 where the python_callable for task
    # 'search_catalog' is missing a required position argument '_'. It is fixed in airflow v2
    patch_airflow_example_dag(dag_bag)

    return make_dagster_repo_from_airflow_dag_bag(
        dag_bag=dag_bag, repo_name=repo_name, use_ephemeral_airflow_db=use_ephemeral_airflow_db
    )


def make_dagster_repo_from_airflow_dags_path(
    dag_path,
    repo_name,
    safe_mode=True,
    use_airflow_template_context=False,
    mock_xcom=False,
    use_ephemeral_airflow_db=True,
    connections=None,
):
    """Construct a Dagster repository corresponding to Airflow DAGs in dag_path.

    Usage:
        Create ``make_dagster_repo.py``:

        .. code-block:: python

            from dagster_airflow.dagster_pipeline_factory import make_dagster_repo_from_airflow_dags_path

            def make_repo_from_dir():
                return make_dagster_repo_from_airflow_dags_path(
                    '/path/to/dags/', 'my_repo_name'
                )

        Use RepositoryDefinition as usual, for example:
        ``dagit -f path/to/make_dagster_repo.py -n make_repo_from_dir``

    Args:
        dag_path (str): Path to directory or file that contains Airflow Dags
        repo_name (str): Name for generated RepositoryDefinition
        include_examples (bool): True to include Airflow's example DAGs. (default: False)
        safe_mode (bool): True to use Airflow's default heuristic to find files that contain DAGs
            (ie find files that contain both b'DAG' and b'airflow') (default: True)
        use_airflow_template_context (bool): If True, will call get_template_context() on the
            Airflow TaskInstance model which requires and modifies the DagRun table. The use_airflow_template_context
            setting is ignored if use_ephemeral_airflow_db is True.
            (default: False)
        mock_xcom (bool): If True, dagster will mock out all calls made to xcom, features that
            depend on xcom may not work as expected. (default: False)
        use_ephemeral_airflow_db (bool): If True, dagster will create an ephemeral sqlite airflow
            database for each run. (default: False)
        connections (List[Connection]): List of Airflow Connections to be created in the Ephemeral
            Airflow DB, if use_emphemeral_airflow_db is False this will be ignored.

    Returns:
        RepositoryDefinition
    """
    check.str_param(dag_path, "dag_path")
    check.str_param(repo_name, "repo_name")
    check.bool_param(safe_mode, "safe_mode")
    check.bool_param(use_airflow_template_context, "use_airflow_template_context")
    mock_xcom = check.opt_bool_param(mock_xcom, "mock_xcom")
    use_ephemeral_airflow_db = check.opt_bool_param(
        use_ephemeral_airflow_db, "use_ephemeral_airflow_db"
    )
    connections = check.opt_list_param(connections, "connections", of_type=Connection)
    # add connections to airflow so that dag evaluation works
    _create_airflow_connections(connections)
    try:
        dag_bag = DagBag(
            dag_folder=dag_path,
            include_examples=False,  # Exclude Airflow example dags
            safe_mode=safe_mode,
        )
    except Exception:
        raise DagsterAirflowError("Error initializing airflow.models.dagbag object with arguments")

    return make_dagster_repo_from_airflow_dag_bag(
        dag_bag=dag_bag,
        repo_name=repo_name,
        use_airflow_template_context=use_airflow_template_context,
        mock_xcom=mock_xcom,
        use_ephemeral_airflow_db=use_ephemeral_airflow_db,
        connections=connections,
    )


def make_dagster_pipeline_from_airflow_dag(
    dag,
    tags=None,
    use_airflow_template_context=False,
    unique_id=None,
    mock_xcom=False,
    use_ephemeral_airflow_db=False,
    connections=None,
):
    """Construct a Dagster pipeline corresponding to a given Airflow DAG.

    Tasks in the resulting pipeline will execute the ``execute()`` method on the corresponding
    Airflow Operator. Dagster, any dependencies required by Airflow Operators, and the module
    containing your DAG definition must be available in the Python environment within which your
    Dagster solids execute.

    To set Airflow's ``execution_date`` for use with Airflow Operator's ``execute()`` methods,
    either:

    1. (Best for ad hoc runs) Run Pipeline with 'default' preset, which sets execution_date to the
        time (in UTC) of pipeline invocation:

        .. code-block:: python

            execute_pipeline(
                pipeline=make_dagster_pipeline_from_airflow_dag(dag=dag),
                preset='default')

    2. Add ``{'airflow_execution_date': utc_date_string}`` to the PipelineDefinition tags. This will
       override behavior from (1).

        .. code-block:: python

            execute_pipeline(
                make_dagster_pipeline_from_airflow_dag(
                    dag=dag,
                    tags={'airflow_execution_date': utc_execution_date_str}
                )
            )

    3. (Recommended) Add ``{'airflow_execution_date': utc_date_string}`` to the PipelineRun tags,
        such as in the Dagit UI. This will override behavior from (1) and (2)


    We apply normalized_name() to the dag id and task ids when generating pipeline name and solid
    names to ensure that names conform to Dagster's naming conventions.

    Args:
        dag (DAG): The Airflow DAG to compile into a Dagster pipeline
        tags (Dict[str, Field]): Pipeline tags. Optionally include
            `tags={'airflow_execution_date': utc_date_string}` to specify execution_date used within
            execution of Airflow Operators.
        use_airflow_template_context (bool): If True, will call get_template_context() on the
            Airflow TaskInstance model which requires and modifies the DagRun table. The use_airflow_template_context
            setting is ignored if use_ephemeral_airflow_db is True.
            (default: False)
        unique_id (int): If not None, this id will be postpended to generated solid names. Used by
            framework authors to enforce unique solid names within a repo.
        mock_xcom (bool): If not None, dagster will mock out all calls made to xcom, features that
            depend on xcom may not work as expected.
        use_ephemeral_airflow_db (bool): If True, dagster will create an ephemeral sqlite airflow
            database for each run
        connections (List[Connection]): List of Airflow Connections to be created in the Ephemeral
            Airflow DB, if use_emphemeral_airflow_db is False this will be ignored.

    Returns:
        pipeline_def (PipelineDefinition): The generated Dagster pipeline

    """
    check.inst_param(dag, "dag", DAG)
    tags = check.opt_dict_param(tags, "tags")
    check.bool_param(use_airflow_template_context, "use_airflow_template_context")
    unique_id = check.opt_int_param(unique_id, "unique_id")
    mock_xcom = check.opt_bool_param(mock_xcom, "mock_xcom")
    use_ephemeral_airflow_db = check.opt_bool_param(
        use_ephemeral_airflow_db, "use_ephemeral_airflow_db"
    )
    connections = check.opt_list_param(connections, "connections", of_type=Connection)

    if IS_AIRFLOW_INGEST_PIPELINE_STR not in tags:
        tags[IS_AIRFLOW_INGEST_PIPELINE_STR] = "true"

    tags = validate_tags(tags)

    pipeline_dependencies, solid_defs = _get_pipeline_definition_args(
        dag=dag,
        use_airflow_template_context=use_airflow_template_context,
        unique_id=unique_id,
        mock_xcom=mock_xcom,
        use_ephemeral_airflow_db=use_ephemeral_airflow_db,
    )

    serialized_connections = []
    for c in connections:
        serialized_connection = {
            "conn_id": c.conn_id,
            "conn_type": c.conn_type,
        }
        if hasattr(c, "login") and c.login:
            serialized_connection["login"] = c.login
        if hasattr(c, "password") and c.password:
            serialized_connection["password"] = c.password
        if hasattr(c, "host") and c.host:
            serialized_connection["host"] = c.host
        if hasattr(c, "schema") and c.schema:
            serialized_connection["schema"] = c.schema
        if hasattr(c, "port") and c.port:
            serialized_connection["port"] = c.port
        if hasattr(c, "extra") and c.extra:
            serialized_connection["extra"] = c.extra
        if hasattr(c, "description") and c.description:
            serialized_connection["description"] = c.description
        serialized_connections.append(serialized_connection)

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
                _create_airflow_connections(
                    [Connection(**c) for c in context.resource_config["connections"]]
                )

            dag_bag = airflow.models.dagbag.DagBag(
                dag_folder=context.resource_config["dag_location"], include_examples=False
            )
            dag = dag_bag.get_dag(context.resource_config["dag_id"])
            execution_date_str = context.dagster_run.tags.get(AIRFLOW_EXECUTION_DATE_STR)
            execution_date = dateutil.parser.parse(execution_date_str)
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

    pipeline_def = PipelineDefinition(
        name=normalized_name(dag.dag_id),
        solid_defs=solid_defs,
        dependencies=pipeline_dependencies,
        mode_defs=[ModeDefinition(resource_defs={"airflow_db": airflow_db})]
        if use_ephemeral_airflow_db
        else [],
        tags=tags,
    )
    return pipeline_def


# Airflow DAG ids and Task ids allow a larger valid character set (alphanumeric characters,
# dashes, dots and underscores) than Dagster's naming conventions (alphanumeric characters,
# underscores), so Dagster will strip invalid characters and replace with '_'
def normalized_name(name, unique_id=None):
    base_name = "airflow_" + "".join(c if VALID_NAME_REGEX.match(c) else "_" for c in name)
    if not unique_id:
        return base_name
    else:
        return base_name + "_" + str(unique_id)


def _get_pipeline_definition_args(
    dag,
    use_airflow_template_context,
    unique_id=None,
    mock_xcom=False,
    use_ephemeral_airflow_db=False,
):
    check.inst_param(dag, "dag", DAG)
    check.bool_param(use_airflow_template_context, "use_airflow_template_context")
    unique_id = check.opt_int_param(unique_id, "unique_id")
    mock_xcom = check.opt_bool_param(mock_xcom, "mock_xcom")
    use_ephemeral_airflow_db = check.opt_bool_param(
        use_ephemeral_airflow_db, "use_ephemeral_airflow_db"
    )

    pipeline_dependencies = {}
    solid_defs = []
    seen_tasks = []

    # To enforce predictable iteration order
    dag_roots = sorted(dag.roots, key=lambda x: x.task_id)
    for task in dag_roots:
        _traverse_airflow_dag(
            dag=dag,
            task=task,
            seen_tasks=seen_tasks,
            pipeline_dependencies=pipeline_dependencies,
            solid_defs=solid_defs,
            use_airflow_template_context=use_airflow_template_context,
            unique_id=unique_id,
            mock_xcom=mock_xcom,
            use_ephemeral_airflow_db=use_ephemeral_airflow_db,
        )
    return (pipeline_dependencies, solid_defs)


def _traverse_airflow_dag(
    dag,
    task,
    seen_tasks,
    pipeline_dependencies,
    solid_defs,
    use_airflow_template_context,
    unique_id,
    mock_xcom,
    use_ephemeral_airflow_db,
):
    check.inst_param(dag, "dag", DAG)
    check.inst_param(task, "task", BaseOperator)
    check.list_param(seen_tasks, "seen_tasks", BaseOperator)
    check.list_param(solid_defs, "solid_defs", OpDefinition)
    check.bool_param(use_airflow_template_context, "use_airflow_template_context")
    unique_id = check.opt_int_param(unique_id, "unique_id")
    mock_xcom = check.opt_bool_param(mock_xcom, "mock_xcom")
    use_ephemeral_airflow_db = check.opt_bool_param(
        use_ephemeral_airflow_db, "use_ephemeral_airflow_db"
    )

    seen_tasks.append(task)
    current_solid = make_dagster_solid_from_airflow_task(
        dag=dag,
        task=task,
        use_airflow_template_context=use_airflow_template_context,
        unique_id=unique_id,
        mock_xcom=mock_xcom,
        use_ephemeral_airflow_db=use_ephemeral_airflow_db,
    )
    solid_defs.append(current_solid)

    if len(task.upstream_list) > 0:
        # To enforce predictable iteration order
        task_upstream_list = sorted(task.upstream_list, key=lambda x: x.task_id)

        pipeline_dependencies[current_solid.name] = {
            "airflow_task_ready": MultiDependencyDefinition(
                [
                    DependencyDefinition(
                        solid=normalized_name(task_upstream.task_id, unique_id),
                        output="airflow_task_complete",
                    )
                    for task_upstream in task_upstream_list
                ]
            )
        }

    # To enforce predictable iteration order
    task_downstream_list = sorted(task.downstream_list, key=lambda x: x.task_id)
    for child_task in task_downstream_list:
        if child_task not in seen_tasks:
            _traverse_airflow_dag(
                dag=dag,
                task=child_task,
                seen_tasks=seen_tasks,
                pipeline_dependencies=pipeline_dependencies,
                solid_defs=solid_defs,
                use_airflow_template_context=use_airflow_template_context,
                unique_id=unique_id,
                mock_xcom=mock_xcom,
                use_ephemeral_airflow_db=use_ephemeral_airflow_db,
            )


@contextmanager
def replace_airflow_logger_handlers():
    prev_airflow_handlers = logging.getLogger("airflow.task").handlers
    try:
        # Redirect airflow handlers to stdout / compute logs
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        root = logging.getLogger("airflow.task")
        root.handlers = [handler]
        yield
    finally:
        # Restore previous log handlers
        logging.getLogger("airflow.task").handlers = prev_airflow_handlers


@contextmanager
def _mock_xcom():
    with patch("airflow.models.TaskInstance.xcom_push"):
        with patch("airflow.models.TaskInstance.xcom_pull"):
            yield


# If unique_id is not None, this id will be postpended to generated solid names, generally used
# to enforce unique solid names within a repo.
def make_dagster_solid_from_airflow_task(
    dag,
    task,
    use_airflow_template_context,
    unique_id=None,
    mock_xcom=False,
    use_ephemeral_airflow_db=False,
):
    check.inst_param(dag, "dag", DAG)
    check.inst_param(task, "task", BaseOperator)
    check.bool_param(use_airflow_template_context, "use_airflow_template_context")
    unique_id = check.opt_int_param(unique_id, "unique_id")
    mock_xcom = check.opt_bool_param(mock_xcom, "mock_xcom")
    use_ephemeral_airflow_db = check.opt_bool_param(
        use_ephemeral_airflow_db, "use_ephemeral_airflow_db"
    )

    @op(
        name=normalized_name(task.task_id, unique_id),
        required_resource_keys={"airflow_db"} if use_ephemeral_airflow_db else None,
        ins={"airflow_task_ready": In(Nothing)},
        out={"airflow_task_complete": Out(Nothing)},
        config_schema={
            "mock_xcom": Field(bool, default_value=mock_xcom),
            "use_ephemeral_airflow_db": Field(bool, default_value=use_ephemeral_airflow_db),
        },
    )
    def _solid(context):  # pylint: disable=unused-argument
        # reloading forces picking up any config that's been set for execution
        importlib.reload(airflow)
        mock_xcom = context.op_config["mock_xcom"]
        use_ephemeral_airflow_db = context.op_config["use_ephemeral_airflow_db"]
        if AIRFLOW_EXECUTION_DATE_STR not in context.pipeline_run.tags:
            raise DagsterInvariantViolationError(
                'Could not find "{AIRFLOW_EXECUTION_DATE_STR}" in {target} tags "{tags}". Please '
                'add "{AIRFLOW_EXECUTION_DATE_STR}" to {target} tags before executing'.format(
                    target="job" if context.pipeline_def.is_graph_job_op_target else "pipeline",
                    AIRFLOW_EXECUTION_DATE_STR=AIRFLOW_EXECUTION_DATE_STR,
                    tags=context.pipeline_run.tags,
                )
            )
        execution_date_str = context.pipeline_run.tags.get(AIRFLOW_EXECUTION_DATE_STR)

        check.str_param(execution_date_str, "execution_date_str")
        try:
            execution_date = dateutil.parser.parse(execution_date_str)
        except ValueError:
            raise DagsterInvariantViolationError(
                'Could not parse execution_date "{execution_date_str}". Please use datetime format '
                "compatible with  dateutil.parser.parse.".format(
                    execution_date_str=execution_date_str,
                )
            )
        except OverflowError:
            raise DagsterInvariantViolationError(
                'Date "{execution_date_str}" exceeds the largest valid C integer on the system.'
                .format(
                    execution_date_str=execution_date_str,
                )
            )

        check.inst_param(execution_date, "execution_date", datetime.datetime)

        with _mock_xcom() if mock_xcom and not use_ephemeral_airflow_db else nullcontext():
            with replace_airflow_logger_handlers():
                if airflow_version >= "2.0.0":
                    if use_ephemeral_airflow_db:
                        dag = context.resources.airflow_db["dag"]
                        dagrun = context.resources.airflow_db["dagrun"]
                        ti = dagrun.get_task_instance(task_id=task.task_id)
                        ti.task = dag.get_task(task_id=task.task_id)
                        ti.run(ignore_ti_state=True)
                    else:
                        # the airflow db is not initialized so no dagrun or task instance exists
                        ti = TaskInstance(
                            task=task,
                            execution_date=execution_date,
                            run_id=f"dagster_airflow_run_{execution_date}",
                        )
                        ti_context = (
                            dagster_get_template_context(ti, task, execution_date)
                            if not use_airflow_template_context
                            else ti.get_template_context()
                        )
                        task.render_template_fields(ti_context)
                        task.execute(ti_context)
                else:
                    if use_ephemeral_airflow_db:
                        dag = context.resources.airflow_db["dag"]
                        dagrun = context.resources.airflow_db["dagrun"]
                        ti = dagrun.get_task_instance(task_id=task.task_id)
                        ti.task = dag.get_task(task_id=task.task_id)
                        ti.run(ignore_ti_state=True)
                    else:
                        ti = TaskInstance(task=task, execution_date=execution_date)
                        ti_context = (
                            dagster_get_template_context(ti, task, execution_date)
                            if not use_airflow_template_context
                            else ti.get_template_context()
                        )
                        task.render_template_fields(ti_context)
                        task.execute(ti_context)
                return None

    return _solid


def dagster_get_template_context(task_instance, task, execution_date):
    """
    Modified from /airflow/models/taskinstance.py to not reference Airflow DB.

    (1) Removes the following block, which queries DB, removes dagrun instances, recycles run_id
    if hasattr(task, 'dag'):
        if task.dag.params:
            params.update(task.dag.params)
        from airflow.models.dagrun import DagRun  # Avoid circular import

        dag_run = (
            session.query(DagRun)
            .filter_by(dag_id=task.dag.dag_id, execution_date=execution_date)
            .first()
        )
        run_id = dag_run.run_id if dag_run else None
        session.expunge_all()
        session.commit()
    (2) Removes returning 'conf': conf which passes along Airflow config
    (3) Removes 'var': {'value': VariableAccessor(), 'json': VariableJsonAccessor()}, which allows
        fetching Variable from Airflow DB
    """
    from airflow import macros

    tables = None
    if "tables" in task.params:
        tables = task.params["tables"]

    params = {}
    run_id = ""
    dag_run = None

    ds = execution_date.strftime("%Y-%m-%d")
    ts = execution_date.isoformat()
    yesterday_ds = (execution_date - datetime.timedelta(1)).strftime("%Y-%m-%d")
    tomorrow_ds = (execution_date + datetime.timedelta(1)).strftime("%Y-%m-%d")

    # For manually triggered dagruns that aren't run on a schedule, next/previous
    # schedule dates don't make sense, and should be set to execution date for
    # consistency with how execution_date is set for manually triggered tasks, i.e.
    # triggered_date == execution_date.
    if dag_run and dag_run.external_trigger:
        prev_execution_date = execution_date
        next_execution_date = execution_date
    else:
        prev_execution_date = task.dag.previous_schedule(execution_date)
        next_execution_date = task.dag.following_schedule(execution_date)

    next_ds = None
    next_ds_nodash = None
    if next_execution_date:
        next_ds = next_execution_date.strftime("%Y-%m-%d")
        next_ds_nodash = next_ds.replace("-", "")
        next_execution_date = pendulum.instance(next_execution_date)

    prev_ds = None
    prev_ds_nodash = None
    if prev_execution_date:
        prev_ds = prev_execution_date.strftime("%Y-%m-%d")
        prev_ds_nodash = prev_ds.replace("-", "")
        prev_execution_date = pendulum.instance(prev_execution_date)

    ds_nodash = ds.replace("-", "")
    ts_nodash = execution_date.strftime("%Y%m%dT%H%M%S")
    ts_nodash_with_tz = ts.replace("-", "").replace(":", "")
    yesterday_ds_nodash = yesterday_ds.replace("-", "")
    tomorrow_ds_nodash = tomorrow_ds.replace("-", "")

    ti_key_str = "{dag_id}__{task_id}__{ds_nodash}".format(
        dag_id=task.dag_id, task_id=task.task_id, ds_nodash=ds_nodash
    )

    if task.params:
        params.update(task.params)

    return {
        "dag": task.dag,
        "ds": ds,
        "next_ds": next_ds,
        "next_ds_nodash": next_ds_nodash,
        "prev_ds": prev_ds,
        "prev_ds_nodash": prev_ds_nodash,
        "ds_nodash": ds_nodash,
        "ts": ts,
        "ts_nodash": ts_nodash,
        "ts_nodash_with_tz": ts_nodash_with_tz,
        "yesterday_ds": yesterday_ds,
        "yesterday_ds_nodash": yesterday_ds_nodash,
        "tomorrow_ds": tomorrow_ds,
        "tomorrow_ds_nodash": tomorrow_ds_nodash,
        "END_DATE": ds,
        "end_date": ds,
        "dag_run": dag_run,
        "run_id": run_id,
        "execution_date": pendulum.instance(execution_date),
        "prev_execution_date": prev_execution_date,
        "prev_execution_date_success": lazy_object_proxy.Proxy(
            lambda: task_instance.previous_execution_date_success
        ),
        "prev_start_date_success": lazy_object_proxy.Proxy(
            lambda: task_instance.previous_start_date_success
        ),
        "next_execution_date": next_execution_date,
        "latest_date": ds,
        "macros": macros,
        "params": params,
        "tables": tables,
        "task": task,
        "task_instance": task_instance,
        "ti": task_instance,
        "task_instance_key_str": ti_key_str,
        "test_mode": task_instance.test_mode,
        "inlets": task.inlets,
        "outlets": task.outlets,
    }
